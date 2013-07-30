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
from libcloud.compute.base import NodeImage, NodeSize, NodeAuthPassword, NodeAuthSSHKey

from .vmware import VMWareDriver
from .bigv import BigVNodeDriver

from yaybu.core.util import memoized
from yaybu.core.state import PartState
from yaybu.util import args_from_expression
from yaybu import base
from yaybu.i18n import _
from yay import errors

logger = logging.getLogger(__name__)


class Compute(base.GraphExternalAction):
    """
    This creates a physical node based on our node record.

        new Compute as mycompute:
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
    def driver(self):
        driver_id = self.params.driver.id.as_string()
        if driver_id.lower() == "vmware":
            Driver = VMWareDriver
        elif driver_id.lower() == "bigv":
            Driver = BigVNodeDriver
        else:
            Driver = get_compute_driver(getattr(ComputeProvider, driver_id))
        driver = Driver(**args_from_expression(Driver, self.params.driver))
        driver.yaybu_ui = self.root.ui
        return driver

    @property
    @memoized
    def state(self):
        return PartState(self.root.state, self.params.name.as_string())

    @property
    def full_name(self):
        return "%s" % str(self.params.name)

    @property
    @memoized
    def images(self):
        return dict((i.id, i) for i in self.driver.list_images())

    @property
    @memoized
    def sizes(self):
        return dict((s.id, s) for s in self.driver.list_sizes())

    def _find_node(self, name):
        existing = [n for n in self.driver.list_nodes() if n.name == name and n.state != NodeState.TERMINATED]
        if len(existing) > 1:
            raise LibcloudError(_("There are already multiple nodes called '%s'") % name)
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
            extra = self.params.image.extra.as_dict(default={}),
            driver = self.driver,
            )

    def _get_size(self):
        try:
            size = self.params.size.as_dict()
        except errors.NoMatching:
            return self.sizes.get('default', None)
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

    def _get_auth(self):
        if 'password' in self.driver.features['create_node']:
            return NodeAuthPassword(self.params.password.as_string())
        elif 'ssh_key' in self.driver.features['create_node']:
            fp = self.root.openers.open(self.params.public_key.as_string())
            return NodeAuthSSHKey(fp.read())

    def _update_node_info(self):
        """ Return a dictionary of information about this node """
        n = self.libcloud_node

        self.state.update(their_name = n.name)

        if n.public_ips:
            self.members.set('public_ip', n.public_ips[0])
        if n.private_ips:
            self.members.set('private_ip', n.private_ips[0])

        self.members.set('fqdn', n.public_ips[0])

        if 'dns_name' in n.extra:
            self.members.set('hostname', n.extra['dns_name'].split(".")[0])
            self.members.set('fqdn', n.extra['dns_name'])
            self.members.set('domain', n.extra['dns_name'].split(".",1)[1])

    def _fake_node_info(self):
        self.members.set('public_ips', '0.0.0.0')
        self.members.set('private_ips', '0.0.0.0')
        self.members.set('fqdn', 'missing-host')

    def test(self):
        with self.root.ui.throbber(_("Testing compute credentials/connectivity")):
            self.driver.list_nodes()

    def apply(self):
        if self.libcloud_node:
            return

        self.state.refresh()

        if "their_name" in self.state:
            self.libcloud_node = self._find_node(self.state.their_name)

        if not self.libcloud_node:
            self.libcloud_node = self._find_node(self.full_name)

        if self.libcloud_node:
            logger.debug("Applying to node %r at %r/%r" % (self.libcloud_node.name, self.libcloud_node.public_ip, self.libcloud_node.private_ip))
            self._update_node_info()
            return

        if self.root.readonly:
            self._fake_node_info()
            return

        logger.debug("Node will be %r" % self.full_name)

        for tries in range(10):
            logger.debug("Creating %r, attempt %d" % (self.full_name, tries))

            with self.root.ui.throbber(_("Creating node '%r'...") % (self.full_name, )) as throbber:
                node = self.driver.create_node(
                    name=self.full_name,
                    image=self._get_image(),
                    size=self._get_size(),
                    auth=self._get_auth(),
                    **args_from_expression(self.driver.create_node, self.params, ignore=("name", "image", "size"), kwargs=getattr(self.driver, "create_node_kwargs", []))
                    )

            logger.debug("Waiting for node %r to start" % (self.full_name, ))

            try:
                with self.root.ui.throbber(_("Waiting for node '%r' to start...") % self.full_name) as throbber:
                    try:
                        import time
                        old_sleep = time.sleep
                        def sleep(amt):
                            throbber.throb()
                            old_sleep(amt)
                        time.sleep = sleep
                        self.libcloud_node, self.ip_addresses = self.driver.wait_until_running([node], wait_period=1, timeout=600)[0]
                    finally:
                        time.sleep = old_sleep

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

    def destroy(self):
        if not self.libcloud_node:
            self.state.refresh()
            if "their_name" in self.state:
                self.libcloud_node = self._find_node(self.state.their_name)
            if not self.libcloud_node:
                self.libcloud_node = self._find_node(self.full_name)
            if not self.libcloud_node:
                return

        with self.root.ui.throbber(_("Destroying node '%r'") % self.full_name) as throbber:
            self.libcloud_node.destroy()

