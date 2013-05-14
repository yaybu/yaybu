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
import logging
import pickle
import subprocess
import StringIO
import sys
import logging.handlers
import getpass

import yay
from yay import ast, errors
from yay.errors import LanguageError, NotFound, NotModified

from yaybu.core import resource
from yaybu import changes, error
from yaybu.error import ParseError, MissingAsset, Incompatible, UnmodifiedAsset
from yaybu.transports import SSHTransport
from yaybu.core.config import Config
from yaybu.core import event


logger = logging.getLogger(__name__)


class Provision(ast.PythonClass):

    """
    Use yaybu to configure a server

    appserver:
        create "yaybu.parts:Provision":
            server:
                fqdn: example.com

            resources: {{ resources }}
    """

    def apply(self):
        hostname = self.params.server.fqdn.as_string()

        logger.info("Updating node %r" % hostname)

        self.host = hostname
        self.user = self.params.server.user.as_string(default='ubuntu')
        self.port = self.params.server.port.as_string(default=22)

        root = self.root
        self.ypath = root.ypath
        self.resume = root.resume
        self.no_resume = root.no_resume
        self.simulate = root.simulate
        self.verbose = root.verbose

        self.options = {}
        if os.path.exists("/etc/yaybu"):
            self.options = yay.load_uri("/etc/yaybu")

        self.transport = SSHTransport(
            context=self,
            verbose = root.verbose,
            simulate = root.simulate,
            env_passthrough = root.env_passthrough
            )

        self.changelog = changes.ChangeLog(self)
        self.changelog.configure_session_logging()

        if not self.simulate and not self.transport.exists(self.get_data_path()):
            self.transport.makedirs(self.get_data_path())

        # This makes me a little sad inside, but the whole
        # context thing needs a little thought before jumping in
        event.state.save_file = self.get_data_path("events.saved")
        event.state.simulate = self.simulate
        event.state.transport = self.transport

        if not self.simulate:
            save_parent = os.path.realpath(os.path.join(event.EventState.save_file, os.path.pardir))
            if not self.transport.exists(save_parent):
                self.transport.makedirs(save_parent)

        try:
            if self.transport.exists(event.EventState.save_file):
                if self.resume:
                    event.state.loaded = False
                elif self.no_resume:
                    if not self.simulate:
                        self.transport.unlink(event.EventState.save_file)
                    event.state.loaded = True
                else:
                    raise error.SavedEventsAndNoInstruction("There is a saved events file - you need to specify --resume or --no-resume")

            # Actually apply the configuration
            bundle = resource.ResourceBundle.create_from_yay_expression(self.params.resources, verbose_errors=self.verbose>2)
            bundle.bind()
            changed = bundle.apply(self, None)

            if not self.simulate and os.path.exists(event.EventState.save_file):
                os.unlink(event.EventState.save_file)

            if not changed:
                # nothing changed
                self.changelog.info("No changes were required")
                result = 254
            else:
                self.changelog.info("All changes were applied successfully")
                result = 0

        except error.ExecutionError, e:
            # this will have been reported by the context manager, so we wish to terminate
            # but not to raise it further. Other exceptions should be fully reported with
            # tracebacks etc automatically
            self.changelog.error("Terminated due to execution error in processing")
            result = e.returncode

        except error.Error, e:
            # If its not an Execution error then it won't have been logged by the
            # Resource.apply() machinery - make sure we log it here.
            self.changelog.write(str(e))
            self.changelog.error("Terminated due to error in processing")
            result = e.returncode

        except SystemExit:
            # A normal sys.exit() is fine..
            raise

        logger.info("Node %r provisioned" % hostname)

        self.metadata['result'] = result

    def get_file(self, filename, etag=None):
        try:
            return self.root.openers.open(filename, etag)
        except NotModified, e:
            raise UnmodifiedAsset(str(e))
        except NotFound, e:
            raise MissingAsset(str(e))

    def get_data_path(self, path=None):
        if not path:
            return "/var/run/yaybu"
        return os.path.join("/var/run/yaybu", path)
