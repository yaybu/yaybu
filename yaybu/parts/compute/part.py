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
from libcloud.compute.base import NodeImage, NodeSize

from ssh.ssh_exception import SSHException
from ssh.rsakey import RSAKey
from ssh.dsskey import DSSKey

from .vmware import VMWareDriver
from yaybu.core.util import memoized
from yaybu.core import runner, runcontext
from yaybu.core.state import PartState

from yay import ast, errors
from yay.config import Config


logger = logging.getLogger(__name__)


class Compute(ast.PythonClass):
    """
    This creates a physical node based on our node record.

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

    def __init__(self, node):
        super(Compute, self).__init__(node)
        self.libcloud_node = None
        self.their_name = None

    @property
    @memoized
    def state(self):
        return PartState(self.root.state, self.params.name.as_string())

    @property
    @memoized
    def driver(self):
        config = self.params["driver"].as_dict()
        driver_name = config['id']
        del config['id']
        if driver_name.lower() == "vmware":
            return VMWareDriver(**config)
        provider = getattr(ComputeProvider, driver_name)
        driver_class = get_compute_driver(provider)
        return driver_class(**config)

    @property
    def full_name(self):
        return "%s/%s" % ("example1", str(self.params.name))

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
    def key(self):
        """ Load the key specified by name. """
        openers = self.root.openers
        saved_exception = None
        for pkey_class in (RSAKey, DSSKey):
            try:
                fp = openers.open(str(self.params.key))
                return pkey_class.from_private_key(fp)
            except SSHException, e:
                saved_exception = e
        raise saved_exception

    def _find_node(self, name):
        existing = [n for n in self.driver.list_nodes() if n.name == name and n.state != NodeState.TERMINATED]
        if len(existing) > 1:
            raise KeyError("There are already multiple nodes called '%s'" % name)
        elif len(existing) == 1:
            logger.debug("Node '%s' already running - not creating new node" % (name, ))
            return existing[0]

    def _get_image(self):
        try:
            image = self.params.image.as_dict()
        except errors.TypeError:
            return self.images.get(self.params.image.as_string(), None)

        id = str(self.params.image.id)
        return NodeImage(
            id = id,
            name = self.params.image.name.as_string(default=id),
            extra = self.params.image.extra.as_dict(),
            driver = self.driver,
            )

    def _get_size(self):
        try:
            size = self.params.size.as_dict()
        except errors.TypeError:
            return self.sizes.get(self.params.size.as_string(), None)

        id = str(self.params.size.id)
        return NodeSize(
            id = id,
            name = self.params.size.name.as_string(default=id),
            ram = self.params.size.ram.as_int(default=0),
            disk = self.params.size.disk.as_int(default=0),
            bandwidth = self.params.bandwidth.as_int(default=0),
            price = self.params.size.price.as_int(default=0),
            driver = self.driver,
            )

    def _update_node_info(self):
        """ Return a dictionary of information about this node """
        n = self.libcloud_node

        self.state.update(their_name = n.name)

        #FIXME: GAH, AWS+libcloud...
        #self.metadata['mapped_as'] = n.public_ips[0]
        #self.metadata['address'] = n.private_ips[0]
        self.metadata['address'] = n.public_ips[0]

        self.metadata['fqdn'] = n.public_ips[0]

        if 'dns_name' in n.extra:
            self.metadata['hostname'] = n.extra['dns_name'].split(".")[0]
            self.metadata['fqdn'] = n.extra['dns_name']
            self.metadata['domain'] = n.extra['dns_name'].split(".",1)[1]

        def interfaces():
            # FIXME: This is almost certainly AWS-specific...
            for i, (pub, priv) in enumerate(zip(n.public_ips, n.private_ips)):
                yield {'name': 'eth%d' % i,
                       'address': priv,
                       'mapped_as': pub}

        self.metadata['interfaces'] = list(interfaces())

    def apply(self):
        if self.libcloud_node:
            return

        self.state.refresh()

        if "their_name" in self.state:
            self.libcloud_node = self._find_node(self.state.their_name)

        if not self.libcloud_node:
            self.libcloud_node = self._find_node(self.full_name)

        if self.libcloud_node:
            self._update_node_info()
            return

        logger.debug("Node will be %r" % self.full_name)

        for tries in range(10):
            logger.debug("Creating %r, attempt %d" % (self.full_name, tries))

            node = self.driver.create_node(
                name=self.full_name,
                image=self._get_image(),
                size=self._get_size(),
                #ex_keyname=self.args['ex_keyname'],
                )

            logger.debug("Waiting for node %r to start" % (self.full_name, ))

            try:
                self.libcloud_node, self.ip_addresses = self.driver.wait_until_running([node], timeout=600)[0]
                logger.debug("Node %r running" % (self.full_name, ))
                # self.their_name = self.libcloud_node.name
                self._update_node_info()
                return

            except LibcloudError:
                logger.warning("Node %r did not start before timeout. retrying." % self.full_name)
                node.destroy()
                continue

            except:
                logger.warning("Node %r had an unexpected error - node will be cleaned up and processing will stop" % self.full_name)
                node.destroy()
                raise
                return

        logger.error("Unable to create node successfully. giving up.")
        raise IOError()


class Provision(ast.PythonClass):

    """
    Use yaybu to configure a server

    prototype ComputeInstance:
        create "yaybu.parts.compute:Compute":
            driver:
                id: AWS
                key: your-amazon-key
                secret: your-amazon-secret
            key: example_key               # This key must be defined in AWS control panel to be able to SSH in
            image: ami-ca1a14be            # Ubuntu 10.04 LTS 64bit EBS
            size: t1.micro                 # Smallest AWS size

    appserver:
        create "yaybu.parts.compute:Provision":
            server: {{ new ComputeInstance(size="t1.medium") }}
            resources: {{ resources }}

    or

    appserver:
        create "yaybu.parts.compute:Provision":
            server:
                fqdn: example.com

            resources: {{ resources }}
    """

    def apply(self):
        hostname = self.params.server.fqdn.as_string()

        logger.info("Updating node %r" % hostname)

        config = Config(searchpath=self.root.openers.searchpath)

        for path in self.params.includes.as_iterable(default=[]):
            config.load_uri(path)

        config.add({"resources": self.params.resources.as_list(default=[])})

        ctx = runcontext.RemoteRunContext(
            None,
            resume=True,
            no_resume=False,
            host = hostname,
            user=self.params.server.user.as_string(default='ubuntu'),
            ypath=self.root.openers.searchpath,
            simulate=self.root.simulate,
            verbose=True, #self.root.verbose,
            env_passthrough=[], #self.root.env_passthrough,
            )
        ctx.set_config(config)

        r = runner.Runner()
        result = r.run(ctx)

        logger.info("Node %r provisioned" % hostname)

        self.metadata['result'] = result

