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


import logging

logger = logging.getLogger("provider")

class User(provider.Provider):

    policies = (resources.user.UserApplyPolicy,)

    @classmethod
    def isvalid(self, *args, **kwargs):
        return super(User, self).isvalid(*args, **kwargs)

    def get_user_info(self, context):
        fields = ("name", "passwd", "uid", "gid", "gecos", "dir", "shell")

        username = self.resource.name.as_string()

        try:
            info_tuple = context.transport.getpwnam(username)
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
            shadow = context.transport.getspnam(username)
            info['passwd'] = shadow.sp_pwd
            if shadow.sp_pwd == "!":
                info['disabled-login'] = True
        except KeyError:
            info['passwd'] = ''
            info['disabled-login'] = False

        return info

    def apply(self, context, output):
        info = self.get_user_info(context)

        if info['exists']:
            command = ['usermod']
            changed = False # we may not change anything yet
        else:
            command = ['useradd', '-N']
            changed = True # we definitely make a change

        name = self.resource.name.as_string()

        fullname = self.resource.fullname.as_string(default='')
        if fullname and info["gecos"] != fullname:
            command.extend(["--comment", self.resource.fullname])
            changed = True

        password = self.resource.password.as_string(default='')
        if password and not info["exists"]:
            command.extend(["--password", self.resource.password])
            changed = True

        home = self.resource.home.as_string(default='')
        if home and info["dir"] != home:
            command.extend(["--home", self.resource.home])
            changed = True

        uid = self.resource.uid.as_string(default='')
        if uid and info["uid"] != int(uid):
            command.extend(["--uid", self.resource.uid])
            changed = True

        gid = self.resource.gid.as_string(default='')
        group = self.resource.group.as_string(default='')
        if gid or group:
            if gid:
                gid = int(gid)
                if gid != info["gid"]:
                    command.extend(["--gid", self.resource.gid])
                    changed = True
            else:
                try:
                    gid = context.transport.getgrnam(group).gr_gid
                except KeyError:
                    if not context.simulate:
                        raise error.InvalidGroup("Group '%s' is not valid" % group)
                    context.changelog.info("Group '%s' doesn't exist; assuming recipe already created it" % group)
                    gid = "GID_CURRENTLY_UNASSIGNED"

                if gid != info["gid"]:
                    command.extend(["--gid", str(gid)])
                    changed = True

        groups = self.resource.groups.resolve()  #as_list(default=[])
        if groups:
            desired_groups = set(groups)
            current_groups = set(g.gr_name for g in context.transport.getgrall() if name in g.gr_mem)

            append = self.resource.append.resolve()
            if append and len(desired_groups - current_groups) > 0:
                if info["exists"]:
                    command.append("-a")
                command.extend(["-G", ",".join(desired_groups - current_groups)])
                changed = True
            elif not append and desired_groups != current_groups:
                command.extend(["-G", ",".join(desired_groups)])
                changed = True

        shell = self.resource.shell.as_string(default='')
        if shell and shell != info["shell"]:
            command.extend(["--shell", str(self.resource.shell)])
            changed = True

        disabled_login = self.resource.disabled_login.resolve()
        if disabled_login and not info["disabled-login"]:
            command.extend(["--password", "!"])
            changed = True

        system = self.resource.system.resolve()
        if info["exists"] == False and system:
            command.extend(["--system"])
            changed = True

        command.extend(["-m", self.resource.name])

        if changed:
            try:
                context.change(ShellCommand(command))
            except error.SystemError as exc:
                raise error.UserAddError("useradd returned error code %d" % exc.returncode)
        return changed


class UserRemove(provider.Provider):

    policies = (resources.user.UserRemovePolicy,)

    @classmethod
    def isvalid(self, *args, **kwargs):
        return super(UserRemove, self).isvalid(*args, **kwargs)

    def apply(self, context, output):
        try:
            existing = context.transport.getpwnam(self.resource.name.as_string().encode("utf-8"))
        except KeyError:
            # If we get a key errror then there is no such user. This is good.
            return False

        command = ["userdel", self.resource.name]

        try:
            context.change(ShellCommand(command))
        except error.SystemError as exc:
            raise error.UserAddError("Removing user %s failed with return code %d" % (self.resource, exc.returncode))

        return True


