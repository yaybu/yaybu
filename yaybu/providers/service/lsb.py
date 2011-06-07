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

import os, shlex, glob

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

    def _enabled_links(self):
        for x in (2, 3, 4, 5):
            yield "/etc/rc%s.d/S%02d%s" % (x, self.resource.priority, self.resource.name)
        for x in (0, 1, 6):
            yield "/etc/rc%s.d/K%02d%s" % (x, 100-self.resource.priority, self.resource.name)

    def _disabled_links(self):
        for x in (0, 1, 2, 3, 4, 5, 6):
            yield "/etc/rc%s.d/K%02d%s" % (x, 100-self.resource.priority, self.resource.name)

    def _update_links(self, context, goal):
        # We turn our "goal" symlinks into a set and use a glob to get a set of
        # all symlinks in an rc.d directory for the current service name
        # The difference between the 2 sets are the links we need to create
        # and the links we need to remove
        target = set(goal)
        current = set(glob.glob("/etc/rc*.d/[SK][0-9][0-9]%s"  % self.resource.name))

        need_deleting = current - target
        need_creating = target - current

        if not need_deleting and not need_creating:
            return False

        for ln in need_deleting:
            context.shell.execute(["rm", ln])

        for ln in need_creating:
            context.shell.execute(["ln", "-s", "/etc/init.d/%s" % self.resource.name, ln])

        return True

    def ensure_enabled(self, context):
        return self._update_links(context, self._enabled_links())

    def ensure_disabled(self, context):
        return self._update_links(context, self._disabled_links())


class Start(_LsbServiceMixin, utils._Start, provider.Provider):
    pass


class Stop(_LsbServiceMixin, utils._Stop, provider.Provider):
    pass


class Restart(_LsbServiceMixin, utils._Restart, provider.Provider):
    pass

