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

import os
import logging
import getpass
import urlparse

import yay
from yay.errors import NotFound, NotModified

from yaybu.provisioner import resource
from yaybu.changes import TextRenderer
from yaybu import error
from yaybu.error import MissingAsset, UnmodifiedAsset
from yaybu import base

from . import event, transports


logger = logging.getLogger(__name__)


class Provision(base.GraphExternalAction):

    """
    Use yaybu to configure a server

    new Provisioner as appserver:
        server:
            fqdn: example.com

        resources: {{ resources }}
    """

    transports = {
        "ssh": transports.SSHTransport,
    }

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
        if os.path.exists("/etc/yaybu"):
            self.options = yay.load_uri("/etc/yaybu")

        if "://" in hostname:
            parsed = urlparse.urlparse(hostname)
            Transport = self.transports[parsed.scheme]
        else:
            Transport = self.transports["ssh"]

        self.transport = Transport(
            context=self,
            verbose=root.verbose,
            simulate=root.simulate,
        )

        with root.ui.throbber("Connect to '%s'" % hostname):
            self.transport.connect()

        if not self.simulate and not self.transport.exists(self.get_data_path()):
            self.transport.makedirs(self.get_data_path())

        # This makes me a little sad inside, but the whole
        # context thing needs a little thought before jumping in
        self.state = event.EventState()
        self.state.save_file = self.get_data_path("events.saved")
        self.state.simulate = self.simulate
        self.state.transport = self.transport

        if not self.simulate:
            save_parent = os.path.realpath(
                os.path.join(self.state.save_file, os.path.pardir))
            if not self.transport.exists(save_parent):
                self.transport.makedirs(save_parent)

        if self.transport.exists(self.state.save_file):
            if self.resume:
                self.state.loaded = False
            elif self.no_resume:
                if not self.simulate:
                    self.transport.unlink(self.state.save_file)
                self.state.loaded = True
            else:
                raise error.SavedEventsAndNoInstruction(
                    "There is a saved events file - you need to specify --resume or --no-resume")

        # Actually apply the configuration
        bundle = resource.ResourceBundle.create_from_yay_expression(
            self.params.resources, verbose_errors=self.verbose > 2)
        bundle.bind()

        with self.root.ui.throbber("Provision %s" % self.host) as throbber:
            changed = bundle.apply(self, throbber)
        self.root.changed(changed)

        if not self.simulate and self.transport.exists(self.state.save_file):
            self.transport.unlink(self.state.save_file)

    def test(self):
        bundle = resource.ResourceBundle.create_from_yay_expression(
            self.params.resources)
        bundle.bind()
        bundle.test(self)

    def change(self, change):
        renderer = TextRenderer.get(change, self.current_output)
        return change.apply(self, renderer)

    def get_file(self, filename, etag=None):
        try:
            return self.root.openers.open(filename, etag)
        except NotModified as e:
            raise UnmodifiedAsset(str(e))
        except NotFound as e:
            raise MissingAsset(str(e))

    def get_data_path(self, path=None):
        if not path:
            return "/var/run/yaybu"
        return os.path.join("/var/run/yaybu", path)
