
from libcloud.compute.types import Provider as ComputeProvider
from libcloud.storage.types import Provider as StorageProvider

from libcloud.compute.providers import get_driver as get_compute_driver
from libcloud.storage.providers import get_driver as get_storage_driver

from libcloud.compute.deployment import MultiStepDeployment, ScriptDeployment, SSHKeyDeployment
from libcloud.storage.types import ContainerDoesNotExistError, ObjectDoesNotExistError
import libcloud.security

import os
import uuid
import logging
import yaml
import StringIO

from yaybu.core.util import memoized

libcloud.security.VERIFY_SSL_CERT = True

logger = logging.getLogger(__name__)

class StateBucket:
    
    """ Abstracts the stored state data. Versioned serialization interface. """
    
    version = 1
    
    def __init__(self, data=None):
        self.nodes = self.load(data)
        
    def register_node(self, role, index, uuid):
        logger.debug("Registering node %r for index %r and role %r" % (uuid, index, role))
        self.nodes[uuid] = (index, role)
        
    def nodes_for_role(self, role):
        for k, v in self.nodes.items():
            if v[1] == role:
                yield v[0], k
        
    def load(self, data):
        if data is None:
            return {}
        d = yaml.load(data)
        v = d['version']
        loader = getattr(self, "load_%s" % v, None)
        if loader is None:
            raise KeyError("No loader available for state file version %r" % v)
        return loader(d)
    
    def load_1(self, data):
        return data['nodes']
        
    def as_stream(self):
        d = {
            'version': self.version,
            'nodes': self.nodes,
            }
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
        logger.debug("Creating node %r with image %r, size %r and keypair %r" % (
            name, image, size, keypair))
        node = self.compute.create_node(
            name=name,
            image=self.images[image],
            size=self.sizes[size],
            ex_keyname=keypair)

        logger.debug("Waiting for node %r to start" % (name, ))
        self.compute._wait_until_running(node)
        logger.debug("Node %r running" % (name, ))
        return self.nodes[name]

class Role:
    
    def __init__(self, name, key, image, size, min_=1, max_=1):
        self.name = name
        self.key = key
        self.image = image
        self.size = size
        self.min = min_
        self.max = max_
        self.nodes = {}

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
            self.cloud_state = StateBucket(data)
            logger.debug("State loaded: %r" % self.cloud_state)
        except ObjectDoesNotExistError:
            logger.debug("State object does not exist in container")
            self.cloud_state = StateBucket()
        for r in self.roles.values():
            logger.debug("Populating nodes for role %r" % (r.name,))
            r.nodes = list(self.cloud_state.nodes_for_role(r.name))
    
    def store_state(self):
        logger.debug("Storing state %r" % self.cloud_state)
        container = self.cloud.get_container(self.state_bucket)
        ### TODO: fetch it first and check it hasn't changed since we last fetched it
        ### TODO: consider supporting merging in of changes
        container.upload_object_via_stream(self.cloud_state.as_stream(), self.cluster, {
        'content_type': 'text/yaml'})

    def provision_roles(self):
        for r in self.roles.values():
            while len(r.nodes) < r.min:
                logger.info("Autoprovisioning node for role %r" % r.name)
                node = self.provision_node(r.name)
                logger.info("Node provisioned: %r" % node)
                
    def register_node(self, role, index, name):
        # should remove the duplication of function between cloud_state and self.roles
        r = self.roles[role]
        r.nodes.append((index, name))
        self.cloud_state.register_node(role, index, name)
    
    def provision_node(self, role):
        # find the lowest unused index
        index = 0
        for n in sorted(self.roles[role].nodes):
            if n[0] == index:
                index += 1
        logger.debug("Index %r chosen for %r" % (index, self.roles[role].nodes))
        name = "%s/%s/%s" % (self.cluster, role, index)
        logger.debug("Node will be %r" % name)
        self.register_node(role, index, name)
        r = self.roles[role]
        self.store_state()
        node = self.cloud.create_node(name, self.images[r.image], self.sizes[r.size], r.key)
        ### TODO: MOLEST NODE
        return node
