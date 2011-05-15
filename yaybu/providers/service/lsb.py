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
    def isvalid(cls, policy, resource, yay):
        if not super(_LsbServiceMixin, cls).isvalid(policy, resource, yay):
            return False
        if getattr(resource, policy.name):
            return False
        if os.path.exists("/sbin/start") and os.path.exists("/etc/init/%s.conf" % resource.name):
            return False
        return os.path.exists("/etc/init.d/%s" % resource.name)

    def get_command(self, action):
        return ["/etc/init.d/%s" % self.resource.name, action]


class Start(_LsbServiceMixin, utils._Start, provider.Provider):
    policies = (resources.service.ServiceStartPolicy,)


class Stop(_LsbServiceMixin, utils._Stop, provider.Provider):
    policies = (resources.service.ServiceStopPolicy,)


class Restart(_LsbServiceMixin, utils._Restart, provider.Provider):
    policies = (resources.service.ServiceRestartPolicy,)

