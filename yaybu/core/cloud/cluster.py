from __future__ import absolute_import

import StringIO
import datetime
import collections
import yaml
import copy
from yaybu.core import remote, runcontext
from . import dependency
from yaybu.core.util import version, get_encrypted

import logging
import abc

from libcloud.storage.types import ContainerDoesNotExistError, ObjectDoesNotExistError
from . import role
from .role import RoleCollectionFactory
from . import dns


from yaybu.roles.compute import api


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
        
        
class Cluster:
    
    """ Built on top of AbstractCloud, a Cluster knows about server roles and
    can create and remove nodes for those roles. """
    
    def __init__(self, cluster_name, filename, argv=None, searchpath=(), verbose=True, state_bucket="yaybu-state"):
        """
        Args:
            cluster_name: The name of the cloud
            filename: The filename of the yay file to be used for the source of roles
            argv: arguments available 
            searchpath: the yaybu search path
            state_bucket: The name of the bucket used to store the state for clusters
        """
        self.name = cluster_name
        self.filename = filename
        self.searchpath = searchpath
        self.verbose = verbose
        self.state_bucket = state_bucket        
        self.argv = argv
        self.roles = None
 
        self.ctx = self.make_context()
        self.create_roles()
        #StateMarshaller(self).load_state()

    def make_context(self, resume=False):
        """ Creates a context suitable for instantiating a cloud """
        ctx = runcontext.RunContext(self.filename, ypath=self.searchpath, verbose=self.verbose, resume=resume)
        config = ctx.get_config()

        config.add({
            'hosts': [],
            'yaybu': {
                'cluster': self.name,
                }
            })

        if self.argv:
            config.set_arguments_from_argv(self.argv)

        if self.roles:
            for r in self.roles:
                r.decorate_config(config)

        return ctx

    def create_roles(self):
        factory = RoleCollectionFactory(self.ctx)
        self.roles = factory.create_collection(self)
        
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
        return
        m = StateMarshaller(self)
        m.store_state()

    def provision(self, dump):
        self.roles.provision(dump)

    def create_node(self, name, image, size, keypair):
        return self.cloud.create_node(name, image, size, keypair)
    
    def update_record(self, ip, zone, name):
        self.cloud.update_record(ip, zone, name)
        
