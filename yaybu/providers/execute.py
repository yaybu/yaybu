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

from yaybu.core import abstract
from yaybu.resource import execute as resource

class Execute(abstract.Provider):

    @classmethod
    def isvalid(self, *args, **kwargs):
        return super(File, self).isvalid(*args, **kwargs)

    def action_create(self, shell):
        if self.resource.creates and os.path.exists(self.resource.creates):
            return

        command = shlex.split(self.resource.command)
        returncode, stdout, stderr = shell.execute(command)

        expected_returncode = self.resource.returncode or 0

        if expected_returncode != returncode:
            raise RuntimeError("%s failed with return code %d" % (self.resource, expected_returncode))

resource.Execute.providers.append(Execute)
