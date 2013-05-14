# Copyright 2011 Isotoma Limited
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

import yay
from yay.errors import LanguageError, NotFound, NotModified

from yaybu.core import resource
from yaybu import changes
from yaybu.core.error import ParseError, MissingAsset, Incompatible, UnmodifiedAsset
from yaybu.transports import SSHTransport
from yaybu.core.config import Config

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


