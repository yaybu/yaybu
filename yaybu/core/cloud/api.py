
from libcloud.compute.types import Provider as ComputeProvider
from libcloud.storage.types import Provider as StorageProvider

from libcloud.compute.providers import get_driver as get_compute_driver
from libcloud.storage.providers import get_driver as get_storage_driver

from libcloud.compute.deployment import MultiStepDeployment, ScriptDeployment, SSHKeyDeployment
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
