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
from yaybu.core import provider

simlog = logging.getLogger("simulation")

class Link(provider.Provider):

    policies = (resources.filesystem.LinkAppliedPolicy,)

    @classmethod
    def isvalid(self, *args, **kwargs):
        return super(Directory, self).isvalid(*args, **kwargs)

    def apply(self, shell):
        name = self.resource.name
        to = self.resource.to
        exists = False
        uid = None
        gid=None
        mode=None

        if os.path.exists(name):
            exists = True

            if os.readlink(name) != to:
                shell.execute(["rm", name])
            else:
                st = os.stat(name)
                uid = st.st_uid
                gid = st.st_gid
                mode = st.st_mode
                if mode > 32767:
                    mode = mode - 32768

        if not exists:
            shell.execute(["ln", "-s", name, self.resource.to])

        if self.resource.owner is not None:
            owner = pwd.getpwnam(self.resource.owner)
            if owner.pw_uid != uid:
                shell.execute(["chown", self.resource.owner, name])

        if self.resource.group is not None:
            group = grp.getgrnam(self.resource.group)
            if group.gr_gid != gid:
                shell.execute(["chgrp", self.resource.group, name])

        if self.resource.mode is not None:
            if mode != self.resource.mode:
                shell.execute(["chmod", "%o" % self.resource.mode, name])
