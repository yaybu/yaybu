# Copyright 2011-13 Isotoma Limited
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
from yay.errors import LanguageError, NotFound, NotModified

from yaybu.core import resource
from yaybu import changes, error
from yaybu.error import ParseError, MissingAsset, Incompatible, UnmodifiedAsset
from yaybu.transports import SSHTransport
from yaybu.core.config import Config
from yaybu.core import event

logger = logging.getLogger("runcontext")


class RunContext(object):

    """ A context object that holds the environment required to run yaybu. """

    simulate = False
    ypath = ()
    verbose = 0

    def __init__(self, root, expression, host, user, Transport=SSHTransport):

        self.root = root
        self.expression = expression

        self.host = host
        self.user = user
        self.port = None

        self.ypath = root.ypath
        self.resume = root.resume
        self.no_resume = root.no_resume
        self.simulate = root.simulate
        self.verbose = root.verbose

        self.options = {}
        if os.path.exists("/etc/yaybu"):
            self.options = yay.load_uri("/etc/yaybu")

        self.transport = Transport(context=self,
            verbose = root.verbose,
            simulate = root.simulate,
            env_passthrough = root.env_passthrough)

        self.changelog = changes.ChangeLog(self)
        self.changelog.configure_session_logging()

    @property
    def bundle(self):
        bundle = resource.ResourceBundle.create_from_yay_expression(self.expression, verbose_errors=self.verbose>2)
        bundle.bind()
        return bundle

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

    def apply(self):
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
            changed = self.bundle.apply(self, None)

            if not self.simulate and os.path.exists(event.EventState.save_file):
                os.unlink(event.EventState.save_file)

            if not changed:
                # nothing changed
                self.changelog.info("No changes were required")
                return 254

            self.changelog.info("All changes were applied successfully")
            return 0

        except error.ExecutionError, e:
            # this will have been reported by the context manager, so we wish to terminate
            # but not to raise it further. Other exceptions should be fully reported with
            # tracebacks etc automatically
            self.changelog.error("Terminated due to execution error in processing")
            return e.returncode
        except error.Error, e:
            # If its not an Execution error then it won't have been logged by the
            # Resource.apply() machinery - make sure we log it here.
            self.changelog.write(str(e))
            self.changelog.error("Terminated due to error in processing")
            return e.returncode
        except SystemExit:
            # A normal sys.exit() is fine..
            raise
        #except:
        #    from yaybu.core.debug import post_mortem
        #    post_mortem()
        #    raise

