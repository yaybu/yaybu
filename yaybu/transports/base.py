# Copyright 2011-2013 Isotoma Limited
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
from ..core import error

class Transport(object):

    """ This object wraps a shell in yet another shell. When the shell is
    switched into "simulate" mode it can just print what would be done. """

    def __init__(self, context, verbose=0, simulate=False, env_passthrough=None):
        self.simulate = context.simulate
        self.verbose = context.verbose
        self.context = context

        self.env_passthrough = ["SSH_AUTH_SOCK"]
        if env_passthrough:
            self.env_passthrough.extend(env_passthrough)
