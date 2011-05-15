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

from yaybu.core import provider
from yaybu.providers.service import utils
from yaybu import resources


class _UpstartServiceMixin(utils._ServiceMixin):

    features = ["restart", ]

    @classmethod
    def isvalid(cls, policy, resource, yay):
        if not super(_UpstartServiceMixin, cls).isvalid(policy, resource, yay):
            return False
        if getattr(resource, policy.name):
            return False
        return os.path.exists("/sbin/start") and os.path.exists("/etc/init/%s.conf" % resource.name)

    def get_command(self, action):
        return ["/sbin/" + action, self.resource.name]


class Start(_UpstartServiceMixin, utils._Start, provider.Provider):
    pass


class Stop(_UpstartServiceMixin, utils._Stop, provider.Provider):
    pass


class Restart(_UpstartServiceMixin, utils._Restart, provider.Provider):
    pass


