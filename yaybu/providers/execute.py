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
from yaybu.changes import ShellCommand


class Execute(provider.Provider):

    policies = (resources.execute.ExecutePolicy,)

    @classmethod
    def isvalid(self, *args, **kwargs):
        return super(Execute, self).isvalid(*args, **kwargs)

    def apply(self, context):
        if self.resource.creates is not None \
           and context.transport.exists(self.resource.creates):
            #logging.info("%r: %s exists, not executing" % (self.resource, self.resource.creates))
            return False

        if self.resource.touch is not None \
                and context.transport.exists(self.resource.touch):
            return False

        if self.resource.unless:
            try:
                if self.transport.execute(self.resource.unless) == 0:
                    return False

            except error.InvalidUser as exc:
                # If a simulation and user missing then we can run our 'unless'
                # guard. We bail out with True so that Yaybu treates the
                # resource as applied.
                if context.simulate:
                    context.changelog.info("User '%s' not found; assuming this recipe will create it" % self.resource.user)
                    return True
                raise

            except error.InvalidGroup as exc:
                # If a simulation and group missing then we can run our 'unless'
                # guard. We bail out with True so that Yaybu treates the
                # resource as applied.
                if context.simulate:
                    context.changelog.info("Group '%s' not found; assuming this recipe will create it" % self.resource.group)
                    return True
                raise

        commands = [self.resource.command] if self.resource.command else self.resource.commands
        for command in commands:
            try:
                context.changelog.apply(ShellCommand(command,
                    cwd=self.resource.cwd or None,
                    env=self.resource.environment or None,
                    user=self.resource.user,
                    group=self.resource.group,
                    umask=self.resource.umask
                    ))
            except error.SystemError as exc:
                rc = exc.returncode
                if self.resource.returncode is not None and rc != self.resource.returncode:
                    raise error.CommandError("%s failed with return code %d" % (self.resource, rc))

        if self.resource.touch is not None:
            context.changelog.apply(ShellCommand(["touch", self.resource.touch]))

        return True


