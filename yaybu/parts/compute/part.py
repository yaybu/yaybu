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
from yaybu.core.util import get_encrypted

from yay import ast, errors


logger = logging.getLogger(__name__)


class Compute(ast.PythonClass):

    """
    mycompute:
        create "yaybu.parts.compute:Compute":
            driver:
                id: AWS
                key: your-amazon-key
                secret: your-amazon-secret

            key: example_key       # This key must be defined in AWS control panel to be able to SSH in
            image: ami-ca1a14be    # Ubuntu 10.04 LTS 64bit EBS
            size: t1.micro         # Smallest AWS size
    """

    keys = []

    def __init__(self, node):
        super(Compute, self).__init__(node)
        self.node = None
        self.their_name = None

    def get_state(self):
        s['their_name'] = self.their_name
        return s

    def set_state(self, state):
        self.their_name = state.get('their_name', self.their_name)

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
    @memoized
    def driver(self):
        if self.driver_name == "vmware":
            return VMWareDriver(**self.args)

        config = self["driver"].resolve() # FIXME: Needs an as_dict()
        self.driver_name = config['id']
        del config['id']

        provider = getattr(ComputeProvider, self.driver_name)
        driver_class = get_compute_driver(provider)
        return driver_class(**config)

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

    def get_part_info(self):
        """ Return a dictionary of information about this node """
        ## TODO
        ## This needs further work!
        ## the interface names should be extracted properly
        ## and the distro, raid and disks sections should be completed
        info = super(Compute, self).get_part_info()

        if not self.node:
            return info

        n = self.node

        info['mapped_as'] = n.public_ips[0]
        info['address'] = n.private_ips[0]
        info['hostname'] = n.extra['dns_name'].split(".")[0]
        info['fqdn'] = n.extra['dns_name']
        info['domain'] = n.extra['dns_name'].split(".",1)[1]

        def interfaces():
            for i, (pub, priv) in enumerate(zip(n.public_ips, n.private_ips)):
                yield {'name': 'eth%d' % i,
                       'address': priv,
                       'mapped_as': pub}

        info['interfaces'] = list(interfaces())

        return info

    @property
    def hostname(self):
        return self.node.extra['dns_name']

    def context(self):
        """ Creates the context used to provision an actual host """
        ctx = self.cluster.make_context(resume=True)
        ctx.set_host(self.hostname)
        return ctx

    def create_runner(self):
        """ Create a runner for the specified host, using the key found in
        the configuration """
        r = remote.RemoteRunner(self.hostname, self.key)
        return r

    def _find_node(self, name):
        existing = [n for n in self.driver.list_nodes() if n.name == name and n.state != NodeState.TERMINATED]
        if len(existing) > 1:
            raise KeyError("There are already multiple nodes called '%s'" % name)
        elif len(existing) == 1:
            logger.debug("Node '%s' already running - not creating new node" % (name, ))
            return existing[0]

    def _get_image(self):
        if isinstance(self.image, dict):
            return node.NodeImage(
                id = self.image.id.get_string(),
                name = self.image.name.get_string(), # else id
                ram = self.image.extra.resolve(), # FIXME: Needs as_dict
                driver = self.driver,
                )
        else:
            return self.images.get(self.image.as_string(), None)

    def _get_size(self):
        if isinstance(self.size, dict):
            return node.NodeSize(
                id = self.size.id.as_string(),
                name = self.size.name.as_string(),    # FIXME: Default to self.size.id
                ram = self.size.ram.as_int(),         # FIXME: Default to 0
                disk = self.size.disk.as_int(),       # FIXME: Default to 0
                bandwidth = self.bandwidth.as_int(),  # FIXME: Default to 0
                price = self.size.price.as_int(),     # FIXME: Default to 0
                driver = self.driver,
                )
        else:
            return self.sizes.get(self.size.as_string(), None)

    def instantiate(self):
        """ This creates a physical node based on our node record. """
        if self.node:
            return

        if self.their_name:
            self.node = self._find_node(self.their_name)

        if not self.node:
            self.node = self._find_node(self.full_name)

        if self.node:
            return

        logger.debug("Node will be %r" % self.full_name)

        for tries in range(10):
            logger.debug("Creating node %r with image %r, size %r and keypair %r" % (
                self.name, self.image, self.size, self.key_name))

            node = self.driver.create_node(
                name=self.full_name,
                image=self._get_image(),
                size=self._get_size(),
                #ex_keyname=self.args['ex_keyname'],
                )

            logger.debug("Waiting for node %r to start" % (self.full_name, ))

            try:
                self.node, self.ip_addresses = self.driver.wait_until_running([node], timeout=600)[0]
            except LibcloudError:
                logger.warning("Node did not start before timeout. retrying.")
                node.destroy()
                continue

            logger.debug("Node %r running" % (self.full_name, ))
            self.their_name = self.node.name
            return

        logger.error("Unable to create node successfully. giving up.")
        raise IOError()

    def provision(self):
        """ Phase 2 of provisioning """
        logger.info("Updating node %r" % self.full_name)

        if dump:
            self.dump(self.context(), "%s.yay" % self.hostname)
        r = self.create_runner()
        r.install_yaybu()
        result = r.run(self.context())

        logger.info("Node %r provisioned" % self.full_name)

        return result

    def destroy(self):
        self.node.destroy()
