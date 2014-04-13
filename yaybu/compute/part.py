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

import abc
import os
import difflib
import logging
import getpass

from libcloud.compute.types import Provider
from libcloud.compute.providers import get_driver
from libcloud.common.types import LibcloudError, InvalidCredsError
from libcloud.compute.types import NodeState
from libcloud.compute.base import NodeImage, NodeSize, NodeAuthPassword, NodeAuthSSHKey

from .vmware import VMWareDriver
from .vbox import VBoxDriver
from .bigv import BigVNodeDriver
from .docker import DockerNodeDriver

from yaybu.core.util import memoized
from yaybu.core.state import PartState
from yaybu.util import get_driver_from_expression, args_from_expression
from yaybu import base, error
from yaybu.i18n import _
from yay import errors

logger = logging.getLogger(__name__)

class LayerException(Exception):
    pass

class NodeFailedToStartException(LayerException):
    pass

class Layer(object):
    """ An underlying implementation of a virtualization layer. There is a
    libcloud implementation and a local layer implementation that take quite
    different configuration and have different semantics. """

    __metaclass__ = abc.ABCMeta

    def __init__(self, original):
        self.original = original
        self.their_name = None
        self.node = None  # was libcloud_node

    @property
    def attached(self):
        """ Return True if we have attached to a node. False if we have yet
        to attach to a node. """
        return self.node is not None

    @abc.abstractmethod
    def load(self, name):
        """ Load and start the specified node, if we can find it. """

    @abc.abstractmethod
    def test(self):
        """ Check that we can connect to the underlying driver successfully.
        Raises an exception on failure, otherwise considered to be a success.
        """

    @abc.abstractmethod
    def name(self):
        """ Return a string representing the name of the underlying node. """

    @abc.abstractmethod
    def location(self):
        """ Return a string representing the location of the node, for example it's IP address """

    @abc.abstractproperty
    def public_ip(self):
        """ The primary public IP address of the node """

    @abc.abstractproperty
    def public_ips(self):
        """ A list of all public IP addresses of the node """

    @abc.abstractproperty
    def private_ip(self):
        """ The primary private IP address of the node """

    @abc.abstractproperty
    def private_ips(self):
        """ A list of all private IP addresses of the node """

    @abc.abstractproperty
    def fqdn(self):
        """ The fully qualified domain name of the node """

    @abc.abstractproperty
    def hostname(self):
        """ The unqualified hostname of the node """

    @abc.abstractproperty
    def domain(self):
        """ The domain name of the node """



class CloudComputeLayer(Layer):

    """
    This creates a physical node based on our node record.

        new Compute as mycompute:
            driver:
                id: AWS
                key: your-amazon-key
                secret: your-amazon-secret

            key: example_key       # This key must be defined in AWS control panel to be able to SSH in
            image: ami-000cea77
            size: t1.micro         # Smallest AWS size
    """

    def __init__(self, original):
        super(CloudComputeLayer, self).__init__(original)
        self.pending_node = None  # a node that hasn't started yet

    def destroy(self):
        self.node.destroy()

    def load(self, name):
        self.node = self._find_node(name)

    def test(self):
        try:
            self.driver.list_nodes()
        except InvalidCredsError:
            logger.exception("Could not connect")
            raise error.InvalidCredError("Unable to login to compute service", anchor=self.original.params.driver.id.anchor)

    @property
    def name(self):
        return self.node.name

    @property
    def location(self):
        return "%r/%r" % (self.node.public_ips, self.node.private_ips)

    @property
    @memoized
    def driver(self):
        """ Find the underlying libcloud driver and marshall the arguments to
        it from whatever is provided in the source yay, by inspection of the
        call signature of the driver. """
        ## This used get_driver_from_expression which has some nice
        ## diff logic we should reuse
        params = self.original.params.driver
        provider = getattr(Provider, self.original.driver_id)
        Driver = get_driver(provider)
        kwargs = getattr(Driver, "kwargs", [])
        args = args_from_expression(Driver, params, ignore=(), kwargs=kwargs)
        driver = Driver(**args)
        driver.yaybu_context = self.original.root
        return driver

    @property
    @memoized
    def images(self):
        return dict((str(i.id), i) for i in self.driver.list_images())

    @property
    @memoized
    def sizes(self):
        return dict((str(s.id), s) for s in self.driver.list_sizes())

    def _find_node(self, name):
        try:
            existing = [
                n for n in self.driver.list_nodes() if n.name == name and n.state != NodeState.TERMINATED]
        except InvalidCredsError:
            raise error.InvalidCredsError(
                "Credentials invalid - unable to check/create '%s'" % self.original.full_name, anchor=None)
        if len(existing) > 1:
            raise LibcloudError(
                _("There are already multiple nodes called '%s'") % name)
        elif not existing:
            return None
        node = existing[0]
        if node.state != NodeState.RUNNING:
            ex_start = getattr(node.driver, "ex_start", None)
            if ex_start is not None:
                logger.debug("Starting node")
                ex_start(node)
            else:
                raise LibcloudError(
                    _("The node is not running and cannot be started"))
        logger.debug(
            "Node '%s' already running - not creating new node" % (name, ))
        return node

    def _get_image_from_id(self, image_id):
        try:
            return self.images[image_id]
        except KeyError:
            raise error.ValueError('Cannot find image "%s" at this host/location' % image_id, anchor=self.original.params.image.inner.anchor)
        except NotImplementedError:
            return NodeImage(
                id=image_id,
                name=image_id,
                extra={},
                driver=self.driver,
            )

    def _get_size_from_id(self, size_id):
        try:
            return self.sizes[size_id]
        except KeyError:
            msg = ['Node size "%s"  not supported by this host/location' % size_id]
            all_sizes = list(self.sizes.keys())
            all_sizes.sort()
            possible = difflib.get_close_matches(size_id, all_sizes)
            if possible:
                msg.append('did you mean "%s"?' % possible[0])
            raise error.ValueError(" - ".join(msg), anchor=self.original.params.size.inner.anchor)
        except NotImplementedError:
            # If backend raises NotImplemented then it doesnt support
            # enumeration.
            return NodeSize(id=size_id, name=size_id, ram=0, disk=0, bandwidth=0, price=0, driver=self.driver)

    def _get_size(self):
        try:
            self.original.params.size.as_dict()

        except errors.NoMatching as e:
            try:
                return self._get_size_from_id('default')
            except error.ValueError:
                pass

            # If the backend doesn't suport a 'default' size then raise the
            # original NoMatching exception
            raise e

        except errors.TypeError:
            return self._get_size_from_id(self.original.params.size.as_string())

        id = str(self.original.params.size.id)
        return NodeSize(
            id=id,
            name=self.original.params.size.name.as_string(default=id),
            ram=self.original.params.size.ram.as_int(default=0),
            disk=self.original.params.size.disk.as_int(default=0),
            bandwidth=self.original.params.bandwidth.as_int(default=0),
            price=self.original.params.size.price.as_int(default=0),
            driver=self.driver,
        )

    def _get_auth(self):
        username = self.original.params.user.as_string(default=getpass.getuser())
        if 'password' in self.driver.features['create_node']:
            password = self.original.params.password.as_string(default=None)
            if password is not None:
                auth = NodeAuthPassword(password)
                auth.username = username
                return auth
        if 'ssh_key' in self.driver.features['create_node']:
            pubkey = self.original.params.public_key.as_string(default=None)
            if pubkey is not None:
                fp = self.original.root.openers.open(os.path.expanduser(pubkey))
                auth = NodeAuthSSHKey(fp.read())
                auth.username = username
                return auth

    @property
    def public_ip(self):
        if self.node.public_ips:
            return self.node.public_ips[0]

    @property
    def public_ips(self):
        if self.node.public_ips:
            return self.node.public_ips

    @property
    def private_ip(self):
        if self.node.private_ips:
            return self.node.private_ips[0]

    @property
    def private_ips(self):
        if self.node.private_ips:
            return self.node.private_ips

    @property
    def hostname(self):
        if 'dns_name' in self.node.extra:
            return self.node.extra['dns_name'].split(".", 1)[0]

    @property
    def domain(self):
        if 'dns_name' in self.node.extra:
            return self.node.extra['dns_name'].split(".", 1)[1]

    @property
    def fqdn(self):
        if 'dns_name' in self.node.extra:
            return self.node.extra['dns_name']

    def create(self):
        kwargs = args_from_expression(self.driver.create_node, self.original.params, ignore=(
            "name", "image", "size"), kwargs=getattr(self.driver, "create_node_kwargs", []))

        if not 'ex_keyname' in kwargs:
            kwargs['auth'] = self._get_auth()

        if 'ex_iamprofile' in kwargs:
            kwargs['ex_iamprofile'] = kwargs['ex_iamprofile'].encode("utf-8")

        image = self._get_image_from_id(self.original.params.image.as_string())
        size = self._get_size()

        self.pending_node = self.driver.create_node(
            name=self.original.full_name,
            image=image,
            state=self.original.state,
            size=size,
            **kwargs
        )

    def wait(self):
        if self.pending_node is None:
            return
        try:
            self.node, ip_addresses = self.driver.wait_until_running([self.pending_node], wait_period=1, timeout=600)[0]
            self.pending_node = None
        except LibcloudError, e:
            logger.exception("LibCloud node did not start in time")
            raise NodeFailedToStartException()

class LocalComputeLayer(Layer):

    drivers = {
        "VMWARE": VMWareDriver,
        "BIGV": BigVNodeDriver,
        "DOCKER": DockerNodeDriver,
        "VBOX": VBoxDriver,
    }

    def _get_image(self):
        """ Image can look like any one of these three formats:

            image: http://server/path/image.img

            image:
              id: image-id

            image:
              distro: ubuntu
              arch: amd64
              release: 12.04

        """
        try:
            # don't find floats
            params = dict((k, self.params.image.get_key(k).as_string()) for k in self.params.image.keys())
        except errors.NoMatching as e:
            try:
                return self._get_image_from_id('default')
            except error.ValueError:
                pass

            # If the backend doesnt support a 'default' image then raise the
            # original NoMatching exception
            raise e

        except errors.TypeError:
            return self._get_image_from_id(self.params.image.as_string())

        if "id" in params:
            return NodeImage(
                id=params["id"],
                name=self.params.image.name.as_string(default=id),
                extra=params,
                driver=self.driver,
            )
        else:
            id = "{distro}-{release}-{arch}".format(**params)
            return NodeImage(
                id=id,
                name=self.params.image.name.as_string(default=id),
                extra=params,
                driver=self.driver
            )

class Compute(base.GraphExternalAction):

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
    @memoized
    def layer(self):
        """ Return the underlying virtualization layer implementation. """
        if self.driver_id in LocalComputeLayer.drivers:
            return LocalComputeLayer(self)
        else:
            return CloudComputeLayer(self)

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

        self.load()
        if self.layer.attached:
            logger.debug("Applying to node %s at %s" % (self.layer.name, self.layer.location))
            return

        if self.root.readonly:
            self.members['public_ip'] = '0.0.0.0'
            self.members['private_ip'] = '0.0.0.0'
            self.members['fqdn'] = 'missing-host'
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

            except Exception as e:
                logger.exception(
                    "Node %r had an unexpected error - node will be cleaned up and processing will stop" % (self.full_name,))
                node.destroy()
                raise


    @property
    def full_name(self):
        return "%s" % str(self.params.name.as_string())

