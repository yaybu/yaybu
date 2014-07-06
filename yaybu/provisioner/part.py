# Copyright 2012-2013 Isotoma Limited
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
import getpass

from fuselage import bundle

from yaybu import base, error
from yay import errors


logger = logging.getLogger(__name__)


class ResourceBundle(bundle.ResourceBundle):

    def add_nodes_from_expression(self, node):
        try:
            node.as_dict()
        except errors.TypeError:
            raise error.ParseError("Not a valid Resource definition", anchor=node.anchor)

        keys = list(node.keys())
        if len(keys) > 1:
            raise error.ParseError("Too many keys in list item", anchor=node.anchor)

        typename = keys[0]
        instances = node.get_key(typename)

        try:
            instances.as_dict()
            iterable = [instances]
        except errors.TypeError:
            iterable = instances.get_iterable()

        # FIXME: We want to inspect the resource kwarg errors ourself so we can map them to nice exceptions
        # Either refactor create or make it throw useful exceptions
        for instance in iterable:
            self.create(typename, instance.as_dict())

    @classmethod
    def create_from_expression(cls, expression):
        b = cls()
        for node in expression.get_iterable():
            b.add_nodes_from_expression(node)
        return b


class Provision(base.GraphExternalAction):

    """
    Use yaybu to configure a server

    new Provisioner as appserver:
        server:
            fqdn: example.com

        resources: {{ resources }}
    """

    def apply(self):
        if self.root.readonly:
            return

        hostname = self.params.server.fqdn.as_string()

        logger.info("Updating node %r" % hostname)

        self.host = hostname
        self.user = self.params.server.user.as_string(
            default=getpass.getuser())
        self.port = self.params.server.port.as_int(default=22)
        self.password = self.params.server.password.as_string(default="")
        self.private_key = self.params.server.private_key.as_string(default="")

        root = self.root
        self.ypath = root.ypath
        self.resume = root.resume
        self.no_resume = root.no_resume
        self.simulate = root.simulate
        self.verbose = root.verbose

        self.options = {}

        with root.ui.throbber("Connect to '%s'" % hostname):
            self.transport.connect()

        # Actually apply the configuration
        bundle = ResourceBundle.create_from_yay_expression(self.params.resources)
        with self.root.ui.throbber("Provision %s" % self.host) as throbber:
            changed = bundle.apply(self, throbber)

        self.root.changed(changed)

    def test(self):
        bundle = ResourceBundle.create_from_yay_expression(self.params.resources)
        bundle.some_sort_of_self_check()  # FIXME
