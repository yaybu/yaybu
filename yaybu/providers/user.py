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
import pwd

from yaybu.core import provider
from yaybu.core import error
from yaybu import resources

import logging

logger = logging.getLogger("provider")

class User(provider.Provider):

    policies = (resources.user.UserApplyPolicy,)

    @classmethod
    def isvalid(self, *args, **kwargs):
        return super(User, self).isvalid(*args, **kwargs)

    def get_user_info(self):
        info = {}
        try:
            info_tuple = pwd.getpwnam(self.resource.name)
        except KeyError:
            return

        for i, field in enumerate(("name", "passwd", "uid", "gid", "gecos", "dir", "shell")):
            info[field] = info_tuple[i]

        return info

    def apply(self, shell):
        info = self.get_user_info()

        # Only support creating users...
        if info:
            return

        command = ["useradd"]

        if self.resource.fullname:
            command.extend(["--comment", self.resource.fullname])

        if self.resource.password:
            command.extend(["--password", self.resource.password])

        if self.resource.home:
            command.extend(["--home", self.resource.home])

        if self.resource.uid:
            command.extend(["--uid", str(self.resource.uid)])

        if self.resource.gid:
            command.extend(["--gid", str(self.resource.gid)])

        command.extend(["-m", self.resource.name])

        returncode, stdout, stderr = shell.execute(command)
        if returncode != 0:
            raise error.ExecutionError("%s failed with return code %d" % (self.resource, returncode))

