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


class Group(provider.Provider):

    policies = (resources.group.GroupApplyPolicy,)

    def get_group_info(self, context):
        fields = ("name", "passwd", "gid", "members",)

        try:
            info_tuple = context.transport.getgrnam(self.resource.name.as_string().encode("utf-8"))
        except KeyError:
            info = dict((f, None) for f in fields)
            info["exists"] = False
            return info

        info = {"exists": True}
        for i, field in enumerate(fields):
            info[field] = info_tuple[i]

        return info

    def apply(self, context, output):
        changed = False
        info = self.get_group_info(context)

        if info["exists"]:
            command = ["groupmod"]
        else:
            command = ["groupadd"]
            changed = True

        gid = self.resource.gid.resolve()
        if gid and info["gid"] != gid:
            command.extend(["--gid", self.resource.gid])

        command.extend([self.resource.name])

        if not changed:
            return False

        try:
            context.change(ShellCommand(command))
        except error.SystemError as exc:
            raise error.InvalidGroup("%s on %s failed with return code %d" % (command[0], self.resource, exc.returncode))

        return True


class GroupRemove(provider.Provider):

    policies = (resources.group.GroupRemovePolicy,)

    def apply(self, context, output):
        try:
            existing = context.transport.getgrnam(self.resource.name.as_string().encode("utf-8"))
        except KeyError:
            # If we get a key errror then there is no such group. This is good.
            return False

        command = ["groupdel", self.resource.name]

        try:
            context.change(ShellCommand(command))
        except error.SystemError as exc:
            raise error.InvalidGroup("groupdel on %s failed with return code %d" % (self.resource, exc.returncode))

        return True
