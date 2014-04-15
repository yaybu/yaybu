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

import logging

from yaybu.core.util import memoized
from yaybu.core.state import PartState
from yaybu import error
from yaybu.i18n import _
from yay import errors
from yaybu.base import GraphExternalAction

from .layer.cloud import CloudComputeLayer
from .layer.base import DriverNotFound, NodeFailedToStartException
from .layer.vbox import VBoxLayer

logger = logging.getLogger(__name__)


class Compute(GraphExternalAction):

    """ Provides the Yaybu interface to the underlying virtualization
    implementation. Handles provision of information out to the rest of the
    yaybu environment and interacting with the UI.

    All actual virtualization activities are delegated to the underlying
    'layer' that provides them. This layer is either a Libcloud interface, or
    a local hypervizor technology.

    We have a single name "DRIVER" within Yaybu for the system that will be
    used, and this could delegate to any kind of layer. e.g. VMWARE uses a
    local VMWare hypervizor, whereas EC2EU uses libcloud to contact Amazon
    Web Services.

    """

    layers = {
        'VBOX': VBoxLayer,
    }
    default_layer = CloudComputeLayer

    @property
    @memoized
    def driver_id(self):
        """ Returns the name of the driver, which could be a plain string, or the id parameter of a driver dictionary. """
        try:
            driver_id = self.params.driver.as_string()
        except errors.TypeError:
            driver_id = self.params.driver.id.as_string()
        return driver_id

    @property
    def driver_params(self):
        try:
            self.params.driver.as_string()
        except errors.TypeError:
            return self.params.driver
        return {}

    @property
    @memoized
    def layer(self):
        """ Return the underlying virtualization layer implementation. """
        if self.driver_id in self.layers:
            return self.layers[self.driver_id](self)
        else:
            return self.default_layer(self)

    @property
    @memoized
    def state(self):
        return PartState(self.root.state, self.full_name)

    def synchronise(self):
        """ Update our members with the appropriate data from the underlying layer. """
        self.state.update(their_name=self.layer.name)
        for i in ['public_ip', 'public_ips',
                 'private_ip', 'private_ips',
                 'fqdn', 'hostname', 'domain']:
            v = getattr(self.layer, i)
            if v is not None:
                self.members[i] = v

    def test(self):
        """ Check that we're able to connect to the underlying
        implementation. Will raise an exception if there is a failure. """
        with self.root.ui.throbber(_("Check compute credentials/connectivity")):
            self.layer.test()

    def destroy(self):
        """ Try to connect the layer successfully, then destroy the underlying node. """
        self.load()
        if not self.layer.attached:
            return
        with self.root.ui.throbber(_("Destroy node %r") % self.full_name):
            self.layer.destroy()

    def load(self):
        if not self.layer.attached:
            self.state.refresh()
            if "their_name" in self.state:
                self.layer.load(self.state.their_name)
        if not self.layer.attached:
            self.layer.load(self.full_name)
        if self.layer.attached:
            self.synchronise()

    def apply(self):
        """ Create or connect the compute node """

        if self.layer.attached:
            return

        try:
            self.load()
        except DriverNotFound:
            raise error.ValueError("%r is not a valid driver" % self.driver_id)
        if self.layer.attached:
            logger.debug("Applying to node %s at %s" % (self.layer.name, self.layer.location))
            return

        if self.root.readonly or self.root.simulate:
            self.members['public_ip'] = '0.0.0.0'
            self.members['private_ip'] = '0.0.0.0'
            self.members['fqdn'] = 'missing-host'
            if self.root.simulate:
                self.root.changed()
            return

        logger.debug("Node will be %r" % self.full_name)

        for tries in range(10):
            logger.debug("Creating %r, attempt %d" % (self.full_name, tries))
            if self.create():
                return
        logger.error("Unable to create node successfully. giving up.")
        raise IOError()

    def create(self):
        with self.root.ui.throbber(_("Create node '%r'") % (self.full_name, )):
            self.layer.create()
            logger.debug("Waiting for node %r to start" % (self.full_name, ))
            try:
                with self.root.ui.throbber(_("Wait for node '%r' to start") % self.full_name):
                    self.layer.wait()
                logger.debug("Node %r running" % (self.full_name, ))
                self.synchronise()
                self.root.changed()
                return True

            except NodeFailedToStartException:
                logger.warning("Node %r did not start before timeout. retrying." % self.full_name)
                self.destroy()
                return False

            except Exception:
                logger.exception(
                    "Node %r had an unexpected error - node will be cleaned up and processing will stop" % (self.full_name,))
                self.node.destroy()
                raise

    @property
    def full_name(self):
        return "%s" % str(self.params.name.as_string())
