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
import stat
import pwd
import grp
import logging

from yaybu import resources
from yaybu.core import provider, error

from files import AttributeChanger

simlog = logging.getLogger("simulation")

class Directory(provider.Provider):

    policies = (resources.filesystem.DirectoryAppliedPolicy,)

    @classmethod
    def isvalid(self, *args, **kwargs):
        return super(Directory, self).isvalid(*args, **kwargs)

    def apply(self, shell):
        changed = False
        ac = AttributeChanger(shell,
                              self.resource.name,
                              self.resource.owner,
                              self.resource.group,
                              self.resource.mode)
        if not os.path.exists(self.resource.name):
            shell.execute(["mkdir", self.resource.name])
            changed = True
        ac.apply(shell)
        if changed or ac.changed:
            return True
        else:
            return False

class RemoveDirectory(provider.Provider):

    policies = (resources.filesystem.DirectoryRemovedPolicy,)

    @classmethod
    def isvalid(self, *args, **kwargs):
        return super(RemoveDirectory, self).isvalid(*args, **kwargs)

    def apply(self, shell):
        if os.path.exists(self.resource.name) and not os.path.isdir(self.resource.name):
            raise error.InvalidProviderError("%r: %s exists and is not a directory" % (self, self.resource.name))
        if os.path.exists(self.resource.name):
            shell.execute(["rmdir", self.resource.name])
            changed = True
        else:
            changed = False
        return changed
