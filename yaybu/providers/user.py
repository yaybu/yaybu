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
try:
    import spwd
except ImportError:
    spwd = None
import grp

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
        fields = ("name", "passwd", "uid", "gid", "gecos", "dir", "shell")

        try:
            info_tuple = pwd.getpwnam(self.resource.name)
        except KeyError:
            info = dict((f, None) for f in fields)
            info["exists"] = False
            info['disabled-login'] = False
            info['disabled-password'] = False
            return info

        info = {"exists": True,
                "disabled-login": False,
                "disabled-password": False,
                }
        for i, field in enumerate(fields):
            info[field] = info_tuple[i]

        try:
            shadow = spwd.getspnam(self.resource.name)
            info['passwd'] = shadow.sp_pwd
            if shadow.sp_pwd == "!":
                info['disabled-login'] = True
        except KeyError:
            info['passwd'] = ''
            info['disabled-login'] = False

        return info

    def apply(self, context):
        if self.resource.password and self.resource.disabled_login:
            raise error.ParseError("Cannot specify password and disabled login for a user")

        info = self.get_user_info()

        if info['exists']:
            command = ['usermod']
            changed = False # we may not change anything yet
        else:
            command = ['useradd', '-N']
            changed = True # we definitely make a change

        if self.resource.fullname and info["gecos"] != self.resource.fullname:
            command.extend(["--comment", self.resource.fullname])
            changed = True

        if self.resource.password and not info["exists"]:
            command.extend(["--password", self.resource.password])
            changed = True

        if self.resource.home and info["dir"] != self.resource.home:
            command.extend(["--home", self.resource.home])
            changed = True

        if self.resource.uid and info["uid"] != self.resource.uid:
            command.extend(["--uid", str(self.resource.uid)])
            changed = True

        if self.resource.gid or self.resource.group:
            if self.resource.gid:
                gid = self.resource.gid
            else:
                try:
                    gid = grp.getgrnam(self.resource.group).gr_gid
                except KeyError:
                    if not context.simulate:
                        raise error.InvalidGroup("Group '%s' is not valid" % self.resource.group)
                    context.changelog.info("Group '%s' doesn't exist; assuming recipe already created it" % self.resource.group)
                    gid = "GID_CURRENTLY_UNASSIGNED"

            if gid != info["gid"]:
                command.extend(["--gid", str(gid)])
                changed = True

        if self.resource.groups:
            desired_groups = set(self.resource.groups)
            current_groups = set(g.gr_name for g in grp.getgrall() if self.resource.name in g.gr_mem)

            if self.resource.append and len(desired_groups - current_groups) > 0:
                if info["exists"]:
                    command.append("-a")
                command.extend(["-G", ",".join(desired_groups - current_groups)])
                changed = True
            elif not self.resource.append and desired_groups != current_groups:
                command.extend(["-G", ",".join(desired_groups)])
                changed = True

        if self.resource.shell != info["shell"]:
            command.extend(["--shell", str(self.resource.shell)])
            changed = True

        if self.resource.disabled_login and not info["disabled-login"]:
            command.extend(["--password", "!"])
            changed = True

        if info["exists"] is False and self.resource.system:
            command.extend(["--system"])
            changed = True

        command.extend(["-m", self.resource.name])

        if changed:
            returncode, stdout, stderr = context.shell.execute(command, exceptions=False)
            if returncode != 0:
                raise error.UserAddError("useradd returned error code %d" % returncode)
        return changed


class UserRemove(provider.Provider):

    policies = (resources.user.UserRemovePolicy,)

    @classmethod
    def isvalid(self, *args, **kwargs):
        return super(UserRemove, self).isvalid(*args, **kwargs)

    def apply(self, context):
        try:
            existing = pwd.getpwnam(self.resource.name.encode("utf-8"))
        except KeyError:
            # If we get a key errror then there is no such user. This is good.
            return False

        command = ["userdel", self.resource.name]

        returncode, stdout, stderr = context.shell.execute(command)
        if returncode != 0:
            raise error.UserAddError("Removing user %s failed with return code %d" % (self.resource, returncode))

        return True


