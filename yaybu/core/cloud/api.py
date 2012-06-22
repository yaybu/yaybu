
from libcloud.compute.types import Provider as ComputeProvider
from libcloud.storage.types import Provider as StorageProvider

from libcloud.compute.providers import get_driver as get_compute_driver
from libcloud.storage.providers import get_driver as get_storage_driver

from libcloud.compute.deployment import MultiStepDeployment, ScriptDeployment, SSHKeyDeployment
from libcloud.storage.types import ContainerDoesNotExistError, ObjectDoesNotExistError
import libcloud.security
from libcloud.common.types import LibcloudError

import os
import uuid
import logging
import yaml
import StringIO
import datetime
import collections
import time

from yaybu.core.util import memoized
from yaybu.core import remote

libcloud.security.VERIFY_SSL_CERT = True

logger = logging.getLogger(__name__)

max_version = 1

class StateMarshaller:
    
    """ Abstracts the stored state data. Versioned serialization interface. """

    """ Storage format is YAML with some header information and then a list of nodes.
    
    Each node is of the form:
    
    {'role': 'xx', 'index': X, 'name': 'XX', 'their_name': 'XX'}
    
    """
   
    version = 1
    
    @classmethod
    def load(self, data):
        """ Returns a dictionary of lists of nodes, indexed by role.
        
        For example, 
        
        {'mailserver': [Node(0, 'cloud/mailserver/0', 'foo'), ...],
         'appserver': [...],
        }
        
        """
        
        if data is None:
            return {}
        d = yaml.load(data)
        v = d['version']
        loader = getattr(self, "load_%s" % v, None)
        if loader is None:
            raise KeyError("No loader available for state file version %r" % v)
        return loader(d)
    
    @classmethod
    def load_1(self, data):
        nodes = collections.defaultdict(lambda: [])
        for n in data['nodes']:
            nodes[n['role']].append(Node(n['index'], n['name'], n['their_name']))
        return nodes
        
    @classmethod
    def as_stream(self, roles):
        d = {
            'version': self.version,
            'timestamp': str(datetime.datetime.now()),
            'nodes': [],
            }
        for r in roles.values():
            for n in r.nodes.values():
                d['nodes'].append({
                    'role': r.name, 
                    'index': n.index, 
                    'name': n.name, 
                    'their_name': n.their_name,
                })
        return StringIO.StringIO(yaml.dump(d))

class Cloud(object):

    """ Adapter of a cloud that provides access to runtime functionality. """

    def __init__(self, compute_provider, storage_provider, args):
        self.compute_provider = compute_provider
        self.storage_provider = storage_provider
        self.args = args

    @property
    @memoized
    def compute(self):
        provider = getattr(ComputeProvider, self.compute_provider)
        driver_class = get_compute_driver(provider)
        return driver_class(**self.args)
    
    @property
    @memoized
    def storage(self):
        provider = getattr(StorageProvider, self.storage_provider)
        driver_class = get_storage_driver(provider)
        return driver_class(**self.args)

    @property
    @memoized
    def images(self):
        return dict((i.id, i) for i in self.compute.list_images())

    @property
    @memoized
    def sizes(self):
        return dict((s.id, s) for s in self.compute.list_sizes())

    @property
    def nodes(self):
        return dict((n.name, n) for n in self.compute.list_nodes())

    def orphans(self):
        """ Return nodes that exist in the cloud for which we do not have
        database records. """
        for r in self.nodes:
            try:
                n = Node.objects.get(pk=r.name)
            except Node.DoesNotExist:
                yield r
                
    def get_container(self, name):
        try:
            container = self.storage.get_container(container_name=name)
        except ContainerDoesNotExistError:
            container = self.storage.create_container(container_name=name)
        return container
            
    def create_node(self, name, image, size, keypair):
        """ This creates a physical node based on our node record. """
        for tries in range(10):
            logger.debug("Creating node %r with image %r, size %r and keypair %r" % (
                name, image, size, keypair))
            node = self.compute.create_node(
                name=name,
                image=self.images[image],
                size=self.sizes[size],
                ex_keyname=keypair)
            logger.debug("Waiting for node %r to start" % (name, ))
            ## TODO: wrap this in a try/except block and terminate
            ## and recreate the node if this fails
            try:
                self.compute._wait_until_running(node, timeout=60)
            except LibcloudError:
                logger.warning("Node did not start before timeout. retrying.")
                node.destroy()
                continue
            if not name in self.nodes:
                logger.debug("Naming fail for new node. retrying.")
                node.destroy()
                continue
            logger.debug("Node %r running" % (name, ))
            return self.nodes[name]
        logger.error("Unable to create node successfully. giving up.")
        raise IOError()

class Node:
    
    """ A runtime record we keep of nodes associated with a role. """
    
    def __init__(self, index, name, their_name):
        
        # the index is a number that identifies which node within this role this is
        # for ease of reference (e.g. appserver/0, appserver/1 etc.) these are re-used
        # as required
        self.index = index
        
        # our full name of the node in the form cluster/role/index
        self.name = name
        
        # the unique name assigned by the cloud
        self.their_name = their_name
    
class Role:
    
    """ A runtime record of roles we know about. Each role has a list of nodes """
    
    def __init__(self, name, key_name, key, image, size, min_=1, max_=1):
        self.name = name
        self.key_name = key_name
        self.key = key
        self.image = image
        self.size = size
        self.min = min_
        self.max = max_
        self.nodes = {} # indexed by the role index

class ScalableCloud:
    
    """ Represents an abstraction of a cloud with it's own names for images
    and sizes and an understanding of roles and scaling. """
    
    def __init__(self, compute_provider, storage_provider, cluster, args, 
                 images, sizes, roles, state_bucket="yaybu-state"):
        self.cloud = Cloud(compute_provider, storage_provider, args)
        self.cluster = cluster
        self.images = images
        self.sizes = sizes
        self.roles = dict((r.name, r) for r in roles)
        self.validate_roles()
        self.state_bucket = state_bucket
        self.load_state()
        
    def get_all_hostnames(self):
        """ Return an iterator of all hostnames in this cluster. """
        for role in self.roles.values():
            for node in role.nodes.values():
                n = self.cloud.nodes[node.their_name]
                yield n.extra['dns_name']
        
    def get_node_info(self, node):
        n = self.cloud.nodes[node.their_name]
        return {
            'public': n.public_ips[0],
            'private': n.private_ips[0],
            'hostname': n.extra['dns_name'].split(".")[0],
            'fqdn': n.extra['dns_name'],
            'domain': n.extra['dns_name'].split(".",1)[1],
            'distro': 'DUMMY',
            'raid': 'DUMMY',
            'disks': 'DUMMY',
            'interfaces': 'DUMMY',
        }
            
    def validate_roles(self):
        for role in self.roles.values():
            if role.image not in self.images:
                raise KeyError("Image %r not known for role %r" % (image, role))
            if role.size not in self.sizes:
                raise KeyError("Size %r not known for role %r" % (size, role))
            if self.images[role.image] not in self.cloud.images:
                raise KeyError("Mapped image %r for %r not known" % (self.images[role.image], role))
            if self.sizes[role.size] not in self.cloud.sizes:
                raise KeyError("Mapped size %r for %r not known" % (self.sizes[role.size], role))
            
    def load_state(self):
        logger.debug("Loading state from bucket")
        container = self.cloud.get_container(self.state_bucket)
        try:
            bucket = container.get_object(self.cluster)
            data = "".join(list(bucket.as_stream()))
            nmap = StateMarshaller.load(data)
            for role, nodes in nmap.items():
                logger.debug("Populating nodes for role %r" % (role,))
                for n in nodes:
                    self.roles[role].nodes[n.name] = n
            logger.debug("State loaded")
        except ObjectDoesNotExistError:
            logger.debug("State object does not exist in container")
    
    def store_state(self):
        logger.debug("Storing state")
        container = self.cloud.get_container(self.state_bucket)
        ### TODO: fetch it first and check it hasn't changed since we last fetched it
        ### TODO: consider supporting merging in of changes
        container.upload_object_via_stream(StateMarshaller.as_stream(self.roles), 
                                           self.cluster, {'content_type': 'text/yaml'})

    def provision_roles(self):
        for r in self.roles.values():
            while len(r.nodes) < r.min:
                logger.info("Autoprovisioning node for role %r" % r.name)
                node = self.provision_node(r.name)
                logger.info("Node provisioned: %r" % node)
                
    def provision_node(self, role):
        """ Actually create the node in the cloud. Update our local runtime
        and update the state held in the cloud. """
        # find the lowest unused index
        index = 0
        for n in sorted(self.roles[role].nodes.keys()):
            if n[0] == index:
                index += 1
        logger.debug("Index %r chosen for %r" % (index, self.roles[role].nodes))
        name = "%s/%s/%s" % (self.cluster, role, index)
        logger.debug("Node will be %r" % name)
        # store a record indicating the node is being created
        self.roles[role].nodes[index] = Node(index, name, None)
        self.store_state()
        r = self.roles[role]
        node = self.cloud.create_node(name, self.images[r.image], self.sizes[r.size], r.key_name)
        # now the node actually exists, update the record
        self.roles[role].nodes[index].their_name = node.name
        self.store_state()
        rnode = self.cloud.nodes[node.name]
        hostname = rnode.extra['dns_name']
        runner = remote.RemoteRunner(hostname, r.key)
        runner.install_yaybu()
        return node
