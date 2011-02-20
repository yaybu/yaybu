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
import grp

from yaybu.core import provider
from yaybu.core import error
from yaybu import resources

import logging

logger = logging.getLogger("provider")

class Group(provider.Provider):

    policies = (resources.group.GroupApplyPolicy,)

    @classmethod
    def isvalid(self, *args, **kwargs):
        return super(Group, self).isvalid(*args, **kwargs)

    def get_group_info(self):
        fields = ("name", "passwd", "gid", "members",)

        try:
            info_tuple = grp.getgrnam(self.resource.name)
        except KeyError:
            info = dict((f, None) for f in fields)
            info["exists"] = False
            return info

        info = {"exists": True}
        for i, field in enumerate(fields):
            info[field] = info_tuple[i]

        return info

    def apply(self, shell):
        info = self.get_user_info()

        command = ["groupmod"] if info["exists"] else ["groupadd"]

        if self.resource.gid and info["gid"] != self.resource.gid:
            command.extend(["--gid", str(self.resource.gid)])

        command.extend([self.resource.name])

        returncode, stdout, stderr = shell.execute(command)
        if returncode != 0:
            raise error.ExecutionError("%s failed with return code %d" % (self.resource, returncode))

        return True

