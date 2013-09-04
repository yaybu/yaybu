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

from yaybu.provisioner import provider
from yaybu.core import error
from yaybu.provisioner import resources
from yaybu.provisioner.changes import ShellCommand


class Execute(provider.Provider):

    policies = (resources.execute.ExecutePolicy,)

    @classmethod
    def isvalid(self, *args, **kwargs):
        return super(Execute, self).isvalid(*args, **kwargs)

    def apply(self, context, output):
        creates = self.resource.creates.as_string()
        if creates and context.transport.exists(creates):
            #logging.info("%r: %s exists, not executing" % (self.resource, self.resource.creates))
            return False

        touch = self.resource.touch.as_string()
        if touch and context.transport.exists(touch):
            return False

        unless = self.resource.unless.as_string()
        if unless:
            try:
                if context.transport.execute(unless,
                        user=self.resource.user.as_string(),
                        cwd=self.resource.cwd.as_string(),
                        )[0] == 0:
                    return False

            except error.InvalidUser as exc:
                # If a simulation and user missing then we can run our 'unless'
                # guard. We bail out with True so that Yaybu treates the
                # resource as applied.
                if context.simulate:
                    context.changelog.info("User '%s' not found; assuming this recipe will create it" % self.resource.user.as_string())
                    return True
                raise

            except error.InvalidGroup as exc:
                # If a simulation and group missing then we can run our 'unless'
                # guard. We bail out with True so that Yaybu treates the
                # resource as applied.
                if context.simulate:
                    context.changelog.info("Group '%s' not found; assuming this recipe will create it" % self.resource.group.as_string())
                    return True
                raise

        command = self.resource.command.as_string()
        if command:
            commands = [self.resource.command]
        else:
            commands = list(self.resource.commands.get_iterable())

        for command in commands:
            try:
                context.change(ShellCommand(command,
                    cwd=self.resource.cwd.as_string() or None,
                    env=self.resource.environment.resolve() or None,
                    user=self.resource.user.as_string(),
                    group=self.resource.group.as_string() or None,
                    umask=self.resource.umask.as_int(),
                    ))
            except error.SystemError as exc:
                returncode = self.resource.returncode.as_int(default=0)
                rc = exc.returncode
                if rc != returncode:
                    raise error.CommandError("%s failed with return code %d" % (self.resource, rc))

        if self.resource.touch.as_string():
            context.change(ShellCommand(["touch", self.resource.touch]))

        return True


