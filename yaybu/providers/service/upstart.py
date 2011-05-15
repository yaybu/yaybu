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


class _LsbServiceMixin(utils._ServiceMixin):

    @classmethod
    def isvalid(self, policy, resource, yay):
        if not super(_LsbServiceMixin, self).isvalid(policy, resource, yay):
            return False
        if getattr(self.resource, policy.name):
            return False
        return os.path.exists("/sbin/start") and os.path.exists("/etc/init/%s.conf" % self.resource.name)

    def get_command(self, action):
        return ["/sbin/" + action, self.resource.name]


class Start(provider.Provider, _LsbServiceMixin, utils._Start):
    policies = (resources.service.ServiceStartPolicy,)


class Stop(provider.Provider, _LsbServiceMixin, utils._Stop):
    policies = (resources.service.ServiceStopPolicy,)


class Restart(provider.Provider, _LsbServiceMixin, utils._Restart):
    policies = (resources.service.ServiceRestartPolicy,)

