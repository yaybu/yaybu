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

from yaybu.changes import TextRenderer
from yaybu import base


logger = logging.getLogger(__name__)


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
        #bundle = ResourceBundle.create_from_yay_expression(
        #    self.params.resources, verbose_errors=self.verbose > 2)

        #with self.root.ui.throbber("Provision %s" % self.host) as throbber:
        #    changed = bundle.apply(self, throbber)
        #self.root.changed(changed)

    def test(self):
        #bundle = ResourceBundle.create_from_yay_expression(
        #    self.params.resources)
        pass

    def change(self, change):
        renderer = TextRenderer.get(change, self.current_output)
        return change.apply(self, renderer)
