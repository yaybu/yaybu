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

from yaybu.core import runcontext

from yay import ast, errors
from yay.config import Config


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

        ctx = runcontext.RunContext(
            self.root,
            self.params.resources,
            host=hostname,
            user=self.params.server.user.as_string(default='ubuntu'),
            )

        result = ctx.apply()

        logger.info("Node %r provisioned" % hostname)

        self.metadata['result'] = result

