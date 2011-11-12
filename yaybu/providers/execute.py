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


class Execute(provider.Provider):

    policies = (resources.execute.ExecutePolicy,)

    @classmethod
    def isvalid(self, *args, **kwargs):
        return super(Execute, self).isvalid(*args, **kwargs)

    def execute(self, shell, command, expected_returncode=None, passthru=False):
        # Filter out empty strings...
        cwd = self.resource.cwd or None
        env = self.resource.environment or None

        returncode, stdout, stderr = shell.execute(command, cwd=cwd, env=env, user=self.resource.user,
            group=self.resource.group, passthru=passthru, exceptions=False)

        if not shell.simulate and expected_returncode != None and expected_returncode != returncode:
            raise error.CommandError("%s failed with return code %d" % (self.resource, returncode))

        return returncode

    def apply(self, context):
        if self.resource.creates is not None \
           and os.path.exists(self.resource.creates):
            #logging.info("%r: %s exists, not executing" % (self.resource, self.resource.creates))
            return False

        if self.resource.touch is not None \
                and os.path.exists(self.resource.touch):
            return False

        if self.resource.unless:
            if self.execute(context.shell, self.resource.unless, passthru=True) == 0:
                return False

        commands = [self.resource.command] if self.resource.command else self.resource.commands
        for command in commands:
            self.execute(context.shell, command, self.resource.returncode)

        if self.resource.touch is not None:
            context.shell.execute(["touch", self.resource.touch])

        return True


