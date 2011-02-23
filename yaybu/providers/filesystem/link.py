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

simlog = logging.getLogger("simulation")

class Link(provider.Provider):

    policies = (resources.filesystem.LinkAppliedPolicy,)

    @classmethod
    def isvalid(self, *args, **kwargs):
        return super(Link, self).isvalid(*args, **kwargs)

    def apply(self, shell):
        name = self.resource.name
        to = self.resource.to
        exists = False
        uid = None
        gid = None
        mode = None
        isalink = False

        try:
            linkto = os.readlink(name)
            isalink = True
        except OSError:
            pass

        if isalink:
            if linkto != to:
                shell.execute(["rm", name])
                isalink = False

        if not isalink:
            if os.path.exists(name):
                shell.execute(["rm", "-rf", name])
            else:
                shell.execute(["ln", "-s", self.resource.to, name])
                isalink = True

        if isalink:
            st = os.lstat(name)
            uid = st.st_uid
            gid = st.st_gid
            mode = stat.S_IMODE(st.st_mode)

        if self.resource.owner is not None:
            owner = pwd.getpwnam(self.resource.owner)
            if owner.pw_uid != uid:
                shell.execute(["chown", "-h", self.resource.owner, name])

        if self.resource.group is not None:
            group = grp.getgrnam(self.resource.group)
            if group.gr_gid != gid:
                shell.execute(["chgrp", "-h", self.resource.group, name])

        if self.resource.mode is not None:
            if mode != self.resource.mode:
                shell.execute(["chmod", "%o" % self.resource.mode, name])

class RemoveLink(provider.Provider):

    policies = (resources.filesystem.LinkRemovedPolicy,)

    @classmethod
    def isvalid(self, *args, **kwargs):
        return super(RemoveLink, self).isvalid(*args, **kwargs)

    def apply(self, shell):
        if os.path.exists(self.resource.name):
            if not os.path.islink(self.resource.name):
                raise error.InvalidProvider("%r: %s exists and is not a link" % (self, self.resource.name))
            shell.execute(["rm", self.resource.name])
            changed = True
        else:
            shell.changelog.info("File %s missing already so not removed" % self.resource.name)
            changed = False
        return changed

