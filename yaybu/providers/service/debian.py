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
import shlex

from yaybu.core import provider
from yaybu.core import error
from yaybu import resources

import logging

logger = logging.getLogger("provider")


class _ServiceMixin(object):

    def is_upstart(self):
        return os.path.exists("/sbin/start") and os.path.exists("/etc/init/%s.conf" % self.resource.name)

    def get_command(self, action):
        if getattr(self.resource, action):
            command = shlex.split(getattr(self.resource, action))
        elif self.is_upstart():
            command = ["/sbin/" + command, self.resource.name]
        else:
            command = ["/etc/init.d/%s" % self.resource.name, command]

        return command

    def status(self, context):
        status = self.get_command("status")
        returncode, stdout, stderr = context.shell.execute(status)

        if self.is_upstart():
            status = stdout.split(" ", 1)[1]
            if status.startswith("start/running"):
                return "running"
            elif status.startswith("stop/waiting"):
                return "stopped"

        return "unknown"

    def do(self, context, action):
        returncode, stdout, stderr = context.shell.execute(command)

        if returncode != 0:
            raise error.CommandError("%s failed with return code %d" % (" ".join(command), returncode))


class Start(provider.Provider, _ServiceMixin):

    policies = (resources.service.ServiceStartPolicy,)

    @classmethod
    def isvalid(self, *args, **kwargs):
        return super(Start, self).isvalid(*args, **kwargs)

    def apply(self, context):
        if self.status() == "running":
            return False

        self.do(context, "start")

        return True


class Stop(provider.Provider, _ServiceMixin):

    policies = (resources.service.ServiceStopPolicy,)

    @classmethod
    def isvalid(self, *args, **kwargs):
        return super(Stop, self).isvalid(*args, **kwargs)

    def apply(self, context):
        if self.status() == "stopped":
            return False

        self.do(context, "stop")

        return True


class Restart(provider.Provider, _ServiceMixin):

    policies = (resources.service.ServiceRestartPolicy,)

    @classmethod
    def isvalid(self, *args, **kwargs):
        return super(Restart, self).isvalid(*args, **kwargs)

    def apply(self, context):
        if self.status() == "stopped":
            self.do(context, "start")
            return True

        if self.resource.supports_restart:
            self.do(context, "restart")
        else:
            self.do(context, "stop")
            self.do(context, "start")

        return True


"""
class Reload(provider.Provider, _ServiceMixin):

    policies = (resources.service.ServiceReloadPolicy,)

    @classmethod
    def isvalid(self, *args, **kwargs):
        return super(Reload, self).isvalid(*args, **kwargs)

    def apply(self, context):
        if self.status() == "running":
            return False

        self.do(context, "start")

        return True
"""

