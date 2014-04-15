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

import getpass
import difflib
import logging
import os

from libcloud.common.types import LibcloudError
from libcloud.compute.types import Provider, InvalidCredsError
from libcloud.compute.base import NodeImage, NodeState, NodeSize
from libcloud.compute import base
from libcloud.compute import providers

from yaybu.core.util import memoized
from yaybu.util import args_from_expression
from yaybu import i18n
from yaybu import error

from yay import errors

from .base import Layer, DriverNotFound

logger = logging.getLogger("yaybu.compute.layer")


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
            raise error.InvalidCredError("Unable to login to compute service", anchor=self.original.params.driver.anchor)

    @property
    def name(self):
        return self.node.name

    @property
    def location(self):
        return "%r/%r" % (self.node.public_ips, self.node.private_ips)

    def driver_class(self):
        provider = getattr(Provider, self.original.driver_id)
        try:
            return providers.get_driver(provider)
        except AttributeError:
            raise DriverNotFound()

    @property
    @memoized
    def driver(self):
        """ Find the underlying libcloud driver and marshall the arguments to
        it from whatever is provided in the source yay, by inspection of the
        call signature of the driver. """
        # This used get_driver_from_expression which has some nice
        # diff logic we should reuse
        params = self.original.driver_params
        Driver = self.driver_class()
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
                i18n._("There are already multiple nodes called '%s'") % name)
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
                    i18n._("The node is not running and cannot be started"))
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
                auth = base.NodeAuthPassword(password)
                auth.username = username
                return auth
        if 'ssh_key' in self.driver.features['create_node']:
            pubkey = self.original.params.public_key.as_string(default=None)
            if pubkey is not None:
                fp = self.original.root.openers.open(os.path.expanduser(pubkey))
                auth = base.NodeAuthSSHKey(fp.read())
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

        if 'ex_keyname' not in kwargs:
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
        except LibcloudError:
            logger.exception("LibCloud node did not start in time")
            raise base.NodeFailedToStartException()
