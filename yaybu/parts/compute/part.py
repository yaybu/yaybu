# Copyright 2012 Isotoma Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import uuid
import logging
import yaml
import StringIO
import datetime
import collections
import time
import copy

from libcloud.compute.types import Provider as ComputeProvider
from libcloud.compute.providers import get_driver as get_compute_driver
from libcloud.common.types import LibcloudError
from libcloud.compute.types import NodeState

from ssh.ssh_exception import SSHException
from ssh.rsakey import RSAKey
from ssh.dsskey import DSSKey

from .vmware import VMWareDriver
from yaybu.core.util import memoized
from yaybu.core import remote
from yaybu.core.cloud.part import Part
from yaybu.core.util import get_encrypted


logger = logging.getLogger(__name__)


class Compute(Part):

    """ A runtime record of roles we know about. Each role has a list of nodes """
    
    def __init__(self, cluster, name, driver, key_name, image, size, depends=()):
        """
        Args:
            name: Part name
            key_name: The name of the key at the cloud provider
            key: The key itself as an SSH object
            image: The name of the image in your local dialect
            size: The size of the image in your local dialect
            depends: A list of roles this role depends on
        """
        super(Compute, self).__init__(cluster, name, depends=depends)
        self.node = None
        self.their_name = None

        self.driver_name = driver['id']
        del driver['id']
        self.args = driver

        self.key_name = key_name
        self.image = image
        self.size = size

    def get_state(self):
        s = super(Compute, self).get_state()
        s['their_name'] = self.their_name
        return s

    def set_state(self, state):
        self.their_name = state.get('their_name', self.their_name)

    @classmethod
    def create_from_yay_expression(klass, cluster, name, v):
        v = v.resolve()
        return klass(
                cluster,
                name,
                get_encrypted(v['driver']),
                get_encrypted(v['key']),
                get_encrypted(v['image']),
                get_encrypted(v.get('size', None)),
                get_encrypted(v.get('depends', ())),
                )

    @property
    def full_name(self):
        return "%s/%s" % (self.cluster.name, self.name)

    @property
    @memoized
    def images(self):
        return dict((i.id, i) for i in self.driver.list_images())

    @property
    @memoized
    def sizes(self):
        return dict((s.id, s) for s in self.driver.list_sizes())

    @property
    def nodes(self):
        return dict((n.name, n) for n in self.driver.list_nodes())

    @property
    @memoized
    def driver(self):
        if self.driver_name == "vmware":
            return VMWareDriver(**self.args)
        provider = getattr(ComputeProvider, self.driver_name)
        driver_class = get_compute_driver(provider)
        return driver_class(**self.args)

    @property
    @memoized
    def key(self):
        """ Load the key specified by name. """
        cluster = self.cluster
        saved_exception = None
        for pkey_class in (RSAKey, DSSKey):
            try:
                file = cluster.ctx.get_file(self.key_name)
                key = pkey_class.from_private_key(file)
                return key
            except SSHException, e:
                saved_exception = e
        raise saved_exception

    def role_info(self):
        """ Return the appropriate stanza from the configuration file """
        return self.cluster.ctx.get_config().mapping.get("roles").resolve()[self.name]
            
    def host_info(self):
        """ Return a dictionary of information about this node """
        ## TODO
        ## This needs further work!
        ## the interface names should be extracted properly
        ## and the distro, raid and disks sections should be completed
        n = self.node
        if not n:
            return {}
        def interfaces():
            for i, (pub, priv) in enumerate(zip(n.public_ips, n.private_ips)):
                yield {'name': 'eth%d' % i,
                       'address': priv,
                       'mapped_as': pub}
        return {
            'rolename': self.name,
            'role': copy.copy(self.role_info()),
            'mapped_as': n.public_ips[0],
            'address': n.private_ips[0],
            'hostname': n.extra['dns_name'].split(".")[0],
            'fqdn': n.extra['dns_name'],
            'domain': n.extra['dns_name'].split(".",1)[1],
            'distro': 'TBC',
            'raid': 'TBC',
            'disks': 'TBC',
            'interfaces': list(interfaces()),
        }

    @property
    def hostname(self):
        return self.node.extra['dns_name']

    def context(self):
        """ Creates the context used to provision an actual host """
        ctx = self.cluster.make_context(resume=True)
        ctx.set_host(self.hostname)
        # ctx.get_config().load_uri("package://yaybu.recipe/host.yay")
        return ctx

    def create_runner(self):
        """ Create a runner for the specified host, using the key found in
        the configuration """
        r = remote.RemoteRunner(self.hostname, self.key)
        return r

    def install_yaybu(self):
        """ Install yaybu on the provided node.
           Args:
                node: a Node instance
            """
        return self.create_runner().install_yaybu()

    def instantiate(self):
        logger.debug("Node will be %r" % self.full_name)

        """ This creates a physical node based on our node record. """

        if self.their_name:
            existing = [n for n in self.driver.list_nodes() if n.name == self.their_name and n.state != NodeState.TERMINATED]
            if len(existing) > 1:
                raise KeyError("There are already multiple nodes called '%s'" % self.their_name)
            elif len(existing) == 1:
                logger.debug("Node '%s' already running - not creating new node" % (self.full_name, ))
                self.node = existing[0]
                return

        existing = [n for n in self.driver.list_nodes() if n.name == self.full_name and n.state != NodeState.TERMINATED]
        if len(existing) > 1:
            raise KeyError("There are already multiple nodes called '%s'" % self.full_name)
        elif len(existing) == 1:
            logger.debug("Node %r already running - not creating new node" % (self.full_name, ))
            self.node = existing[0]
            self.their_name = self.node.name
            return

        if isinstance(self.image, dict):
            image = node.NodeImage(
                id = self.image['id'],
                name = self.image.get('name', self.image['id']),
                ram = self.image.get('extra', {}),
                driver = self.driver,
                )
        else:
            image = self.images.get(self.image, None)

        if isinstance(self.size, dict):
            size = node.NodeSize(
                id = self.size['id'],
                name = self.size.get('name', self.size['id']),
                ram = self.size.get('ram', 0),
                disk = self.size.get('disk', 0),
                bandwidth = self.size.get('bandwidth', 0),
                price = self.size.get('price', 0),
                driver = self.driver,
                )
        else:
            size = self.sizes.get(self.size, None)

        for tries in range(10):
            logger.debug("Creating node %r with image %r, size %r and keypair %r" % (
                self.name, self.image, self.size, self.key_name))

            node = self.driver.create_node(
                name=self.full_name,
                image=image,
                size=size,
                #ex_keyname=self.args['ex_keyname'],
                )

            logger.debug("Waiting for node %r to start" % (self.full_name, ))
            ## TODO: wrap this in a try/except block and terminate
            ## and recreate the node if this fails
            try:
                self.node, self.ip_addresses = self.driver._wait_until_running(node, timeout=600)
            except LibcloudError:
                logger.warning("Node did not start before timeout. retrying.")
                node.destroy()
                continue
            logger.debug("Node %r running" % (self.full_name, ))

            self.their_name = self.node.name

            self.install_yaybu()
            logger.info("Node provisioned: %r" % node)
            return
 
        logger.error("Unable to create node successfully. giving up.")
        raise IOError()

    def get_part_info(self):
        cfg = super(Computer, self).get_part_info()
        if self.node is not None:
            pass
        return cfg

    def provision(self, dump=False):
        """ Phase 2 of provisioning """
        logger.info("Updating host %r" % self.node)
        if dump:
            self.dump(self.context(), "%s.yay" % self.hostname)
        r = self.create_runner()
        result = r.run(self.context())
        return result

    def destroy(self):
        self.node.destroy()



