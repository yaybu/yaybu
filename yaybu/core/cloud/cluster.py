from __future__ import absolute_import

import StringIO
import datetime
import collections
import yaml
import copy
from yaybu.core import remote, runcontext
from . import api
from . import dependency
from yaybu.core.util import version, get_encrypted

import logging
import abc

from libcloud.storage.types import ContainerDoesNotExistError, ObjectDoesNotExistError
from . import role
from . import node
from .role import RoleCollectionFactory
from . import dns


logger = logging.getLogger(__name__)

class StateMarshaller:
    
    """ Abstracts the stored state data. Versioned serialization interface.
    Storage format is YAML with some header information and then a list of
    nodes.
    """
   
    version = 1
    """ The version that will be written when saved. """
    
    def __init__(self, cluster):
        self.cluster = cluster
    
    def load(self, data):
        """ Select the appropriate loader based on the version """
        if data is None:
            return {}
        d = yaml.load(data)
        v = d['version']
        loader = getattr(self, "load_%s" % v, None)
        if loader is None:
            raise KeyError("No loader available for state file version %r" % v)
        return loader(d)
    
    def load_1(self, data):
        """ Returns a dictionary of lists of nodes, indexed by role. For example, 
        {'mailserver': [Node(0, 'cloud/mailserver/0', 'foo'), ...],
         'appserver': [...],
        }  """
        
        nodes = collections.defaultdict(lambda: [])
        for n in data['nodes']:
            nodes[n['role']].append((n['index'], n['name'], n['their_name']))
        return nodes
        
    def as_stream(self, roles):
        d = {
            'version': self.version,
            'timestamp': str(datetime.datetime.now()),
            'nodes': [],
            }
        for r in roles:
            for n in r.nodes:
                d['nodes'].append({
                    'role': r.name, 
                    'index': n.index, 
                    'name': n.name, 
                    'their_name': n.their_name,
                })
        return StringIO.StringIO(yaml.dump(d))

    def load_state(self):
        """ Load the state file from the cloud """
        logger.debug("Loading state from bucket")
        container = self.cluster.cloud.get_container(self.cluster.state_bucket)
        try:
            bucket = container.get_object(self.cluster.name)
            data = "".join(list(bucket.as_stream()))
            nmap = self.load(data)
            for role, nodes in nmap.items():
                logger.debug("Finding nodes for role %r" % (role,))
                for index, name, their_name in nodes:
                    self.cluster.roles[role].add_node(index, name, their_name)
            logger.debug("State loaded")
        except ObjectDoesNotExistError:
            logger.debug("State object does not exist in container")
    
    def store_state(self):
        """ Store the state in the cloud """
        logger.debug("Storing state")
        container = self.cluster.cloud.get_container(self.cluster.state_bucket)
        ### TODO: fetch it first and check it hasn't changed since we last fetched it
        ### TODO: consider supporting merging in of changes
        container.upload_object_via_stream(self.as_stream(self.cluster.roles), 
                                           self.cluster.name, {'content_type': 'text/yaml'})
        
class AbstractCloud:
    
    """ An abstraction built on top of the libcloud api. Allows you to have
    your own internal names for images and sizes, to increase portability.
    """
    
    def __init__(self, compute_provider, storage_provider, dns_provider, images, sizes, args=(), compute_args=(), storage_args=()):
        """
        Args:
            compute_provider: The name of the compute provider in libcloud
            storage_provider: the name of the storage provider in libcloud
            dns_provider: The name of the dns provider in libcloud, or 'route53'
            args: A dictionary of arguments to provide to the providers
            images: A dictionary of images that maps your names to the providers names
            sizes: A dictionary of sizes that maps your names to the providers names
        """
        self.cloud = api.Cloud(compute_provider, storage_provider, dns_provider, args, compute_args, storage_args)
        # DUMMY provider has numeric images and sizes
        self.images = dict([(x,str(y)) for (x,y) in images.items()])
        self.sizes = dict([(x,str(y)) for (x,y) in sizes.items()])
        
    @property
    def nodes(self):
        return self.cloud.nodes
    
    def get_container(self, name):
        return self.cloud.get_container(name)
            
    def validate(self, image, size):
        """ Validate that the image and size requested is valid """
        if image not in self.images:
            raise KeyError("Image %r not known" % (image,))
        
        if size not in self.sizes:
            raise KeyError("Size %r not known" % (size,))
        
        if self.images[image] not in self.cloud.images:
            raise KeyError("Mapped image %r not known" % (self.images[image], ))
        
        if self.sizes[size] not in self.cloud.sizes:
            raise KeyError("Mapped size %r not known" % (self.sizes[role.size], ))
            
    def create_node(self, name, image, size, keypair):
        return self.cloud.create_node(
            name,
            self.images[image],
            self.sizes[size],
            keypair)
    
    def destroy_node(self, nodename):
        node = self.cloud.nodes[nodename]
        self.cloud.destroy_node(node)
    
    def update_record(self, ip, zone, name):
        self.cloud.update_record(ip, zone, name)
        
class ConfigDecorator:
    
    """ Decorates a yaybu configuration with the available details for a cluster. """
    
    def __init__(self, cluster):
        self.cluster = cluster
        
    def decorate(self, config):
        """ Update the configuration with the details for all running nodes """
        new_cfg = {'hosts': [],
                   'yaybu': {
                       'provider': self.cluster.provider,
                       'cluster': self.cluster.name,
                       }
                   }

        config.add(new_cfg)

        if self.cluster.cloud is not None:
            roles = config.mapping.get('roles').resolve()
            for role in self.cluster.roles:
                for node in role.nodes:
                    struct = node.host_info()
                    new_cfg['hosts'].append(struct)

        config.add(new_cfg)
        
class Cluster:
    
    """ Built on top of AbstractCloud, a Cluster knows about server roles and
    can create and remove nodes for those roles. """
    
    def __init__(self, provider, cluster_name, filename, argv=None, searchpath=(), verbose=True, state_bucket="yaybu-state"):
        """
        Args:
            name: The name of the cloud
            cloud: An AbstractCloud instance
            filename: The filename of the yay file to be used for the source of roles
            argv: arguments available 
            searchpath: the yaybu search path
            state_bucket: The name of the bucket used to store the state for clusters
        """
        self.provider = provider
        self.name = cluster_name
        self.filename = filename
        self.searchpath = searchpath
        self.verbose = verbose
        self.state_bucket = state_bucket        
        self.argv = argv
        self.cloud = None
        
        self.ctx = self.make_context()
        self.create_cloud()
        self.create_roles()
        StateMarshaller(self).load_state()

    def make_context(self, resume=False):
        """ Creates a context suitable for instantiating a cloud """
        ctx = runcontext.RunContext(self.filename, ypath=self.searchpath, verbose=self.verbose, resume=resume)
        if self.argv:
            ctx.get_config().set_arguments_from_argv(self.argv)
        decorator = ConfigDecorator(self)
        decorator.decorate(ctx.get_config())
        return ctx

    def create_cloud(self):
        clouds = self.ctx.get_config().mapping.get('clouds').resolve()
        p = clouds.get(self.provider, None)
        if p is None:
            raise KeyError("provider %r not found" % self.provider)
        cloud = AbstractCloud(
            get_encrypted(p['providers']['compute']),
            get_encrypted(p['providers']['storage']),
            get_encrypted(p['providers']['dns']),
            get_encrypted(p['images']),
            get_encrypted(p['sizes']),
            args=get_encrypted(p.get('args', {})), 
            compute_args=get_encrypted(p.get('compute_args', {})),
            storage_args=get_encrypted(p.get('storage_args', {})),
            )
        self.cloud = cloud
        
    def create_roles(self):
        factory = RoleCollectionFactory(self.ctx, self.provider)
        self.roles = factory.create_collection(self)
        for r in self.roles:
            self.cloud.validate(r.image, r.size)        
        
    def delete_cloud(self, ctx, provider, cluster_name, filename):
        clouds = ctx.get_config().mapping.get('clouds').resolve()
        p = clouds.get(provider, None)
        if p is None:
            raise KeyError("provider %r not found" % provider)
        raise NotImplementedError

    def dump(self, ctx, filename):
        """ Dump the configuration in a raw form """
        cfg = ctx.get_config().get()
        open(filename, "w").write(yay.dump(cfg))
        
    def commit(self):
        """ Store state to permanent storage """
        m = StateMarshaller(self)
        m.store_state()

    @property
    def libcloud_nodes(self):
        return self.cloud.nodes
    
    def provision(self, dump):
        self.roles.provision(dump)

    def create_node(self, name, image, size, keypair):
        return self.cloud.create_node(name, image, size, keypair)
    
    def update_record(self, ip, zone, name):
        self.cloud.update_record(ip, zone, name)
        
