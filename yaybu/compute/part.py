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
from yaybu import base

from .layer.cloud import CloudComputeLayer
from .layer.base import DriverNotFound, NodeFailedToStartException
from .layer.vbox import VBoxLayer
from .layer.vmware import VMWareLayer

logger = logging.getLogger(__name__)


class ActionContext(base.ActionContext):

    def __init__(self, node):
        super(ActionContext, self).__init__(node)
        self.simulate = node.root.simulate
        self.ui = node.root.ui
        self.state = node.state

    def update_from_layer(self):
        print type(self.layer)
        for i in ['public_ip', 'public_ips',
                 'private_ip', 'private_ips',
                 'fqdn', 'hostname', 'domain']:
            v = getattr(self.layer, i)
            if v is not None:
                self.outputs[i] = v


class Compute(base.Part):

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

    ActionContext = ActionContext

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
    def state(self):
        return PartState(self.root.state, self.full_name)

    @property
    def full_name(self):
        return "%s" % str(self.params.name.as_string())


class SetupLayer(base.Action):

    part = Compute

    layers = {
        'VBOX': VBoxLayer,
        'VMWARE': VMWareLayer,
    }
    default_layer = CloudComputeLayer

    def apply(self, context):
        try:
            if context.node.driver_id in self.layers:
                context.layer = self.layers[context.node.driver_id](context.node)
            else:
                context.layer = self.default_layer(context.node)
        except DriverNotFound:
            raise error.ValueError("Driver not found")


class GetCurrentState(base.Action):

    """
    Based on the information in the config and any information in the state
    data find metadata on a given VM.
    """

    part = Compute
    dependencies = [SetupLayer]

    def apply(self, context):
        context.outputs['public_ip'] = '0.0.0.0'
        context.outputs['private_ip'] = '0.0.0.0'
        context.outputs['fqdn'] = 'missing-host'

        # If our local state file knows the unique name for the VM (which might
        # be different from the name we asked for in the config) then look to see if it
        # still exists - it might have gone away when we werent looking.
        if not context.layer.attached:
            context.state.refresh()
            if "their_name" in context.state:
                context.layer.load(context.state.their_name)

        # If we can't find a VM based on the state file then see if we can find one based on
        # the name in the config. This might work for platforms that do use our name as the
        # canonical ID - and means 2 people can both apply a config without needing shared state
        if not context.layer.attached:
            context.layer.load(context.node.full_name)
            context.state.update(their_name=context.node.full_name)

        # If we have managed to find a Compute resource then update the context with all the
        # information we've been able to retrieve.
        if context.layer.attached:
            context.update_from_layer()
            logger.debug("Found existing node %s at %s" % (context.layer.name, context.layer.location))


class Test(base.Action):

    """
    Test connectivity
    """

    name = "test"
    part = Compute
    dependencies = [GetCurrentState]

    def apply(self, context):
        """ Check that we're able to connect to the underlying
        implementation. Will raise an exception if there is a failure. """
        with context.ui.throbber(_("Check compute credentials/connectivity")):
            context.layer.test()


class Sync(base.Action):

    """
    Compare the params in the graph to the actual state in the cloud provider
    and create a new Compute node as required.
    """

    name = "sync"
    part = Compute
    dependencies = [GetCurrentState]

    def apply(self, context):
        """ Create or connect the compute node """
        if context.layer.attached:
            # FIXME: One day inspect to see if Compute node needs re-provisioning
            return

        logger.debug("Node will be %r" % context.node.full_name)

        for tries in range(10):
            logger.debug("Creating %r, attempt %d" % (context.node.full_name, tries))
            if self.create(context):
                return

        logger.error("Unable to create node successfully. giving up.")
        raise IOError()

    def create(self, context):
        with context.ui.throbber(_("Create node '%r'") % (context.node.full_name, )):
            if not context.simulate:
                context.layer.create()
            context.changed = True

        if context.simulate:
            return True

        logger.debug("Waiting for node %r to start" % (context.node.full_name, ))
        try:
            with context.ui.throbber(_("Wait for node '%r' to start") % context.node.full_name):
                context.layer.wait()
            logger.debug("Node %r running" % (context.node.full_name, ))
            context.update_from_layer()
            context.changed = True
            return True

        except NodeFailedToStartException:
            logger.warning("Node %r did not start before timeout. retrying." % context.node.full_name)
            context.layer.destroy()
            return False

        except Exception:
            logger.exception(
                "Node %r had an unexpected error - node will be cleaned up and processing will stop" % (context.node.full_name,))
            context.layer.destroy()
            raise


class Destroy(base.Action):

    name = "destroy"
    part = Compute
    dependencies = [GetCurrentState]

    def apply(self, context):
        """ Try to connect the layer successfully, then destroy the underlying node. """
        if not context.layer.attached:
            return
        with context.ui.throbber(_("Destroy node %r") % context.node.full_name):
            context.layer.destroy()


class EstimateCost(base.Action):

    name = "estimate_cost"
    part = Compute
    dependencies = [GetCurrentState]

    def apply(self, context):
        # FIXME: Do something nice with this
        print context.layer.price
