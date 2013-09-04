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

from yaybu import error
from yaybu.provisioner import resources
from yaybu.provisioner.changes import ShellCommand


# http://upstart.ubuntu.com/getting-started.html
# http://upstart.ubuntu.com/cookbook/#initctl-status

class _ServiceMixin(object):

    features = []

    def status(self, context):
        running = self.resource.running.as_string(default='')
        if running:
            rc, stdout, stderr = context.transport.execute(running)
            if rc == 0:
                return "running"
            else:
                return "not-running"

        pidfile = self.resource.pidfile.as_string(default='')
        if not pidfile:
            return "unknown"

        if not context.transport.exists(pidfile):
            return "not-running"

        pid = context.transport.get(pidfile).strip()
        try:
            pid = int(pid)
        except:
            return "unknown"

        if context.transport.execute(["kill", "-0", str(pid)])[0] == 0:
            return "running"
        else:
            return "not-running"

    def do(self, context, action):
        try:
            context.change(ShellCommand(self.get_command(action)))
        except error.SystemError as exc:
            raise error.CommandError("%s failed with return code %d" % (action, exc.returncode))

    def ensure_enabled(self, context):
        pass

    def ensure_disabled(self, context):
        pass


class _Start(object):

    policies = (resources.service.ServiceStartPolicy,)

    def apply(self, context, output):
        changed = self.ensure_enabled(context)

        if self.status(context) == "running":
            return changed

        self.do(context, "start")

        return True


class _Stop(object):

    policies = (resources.service.ServiceStopPolicy,)

    def apply(self, context, output):
        changed = self.ensure_disabled(context)

        if self.status(context) == "not-running":
            return changed

        self.do(context, "stop")

        return True


class _Restart(object):

    policies = (resources.service.ServiceRestartPolicy,)

    def apply(self, context, output):
        changed = self.ensure_enabled(context)

        if self.status(context) == "not-running":
            self.do(context, "start")
            return True

        if "restart" in self.features:
            self.do(context, "restart")
        else:
            self.do(context, "stop")
            self.do(context, "start")

        return True


