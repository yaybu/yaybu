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

from yaybu import error
from yaybu.provisioner import resources
from yaybu.provisioner import provider
from yaybu.provisioner.changes import ShellCommand


class Mount(provider.Provider):

    policies = (resources.mount.MountPolicy,)

    def check_path(self, context, directory):
        if context.transport.isdir(directory):
            return

        simulate = context.simulate
        transport = context.transport
        frags = directory.split("/")
        path = "/"
        for i in frags:
            path = os.path.join(path, i)
            if not transport.exists(path):
                if self.resource.parents.resolve():
                    return
                if simulate:
                    return
                raise error.PathComponentMissing(path)
            if not transport.isdir(path):
                raise error.PathComponentNotDirectory(path)

    def get_all_active_mounts(self, context):
        path = context.transport.get("/proc/mounts")
        d = {}
        for line in path.split("\n"):
            if not line.strip():
                continue

            split = line.split()
            d[split[1]] = {
                "fs_type": split[0],
                "mountpoint": split[1],
                "device": split[2],
                "options": split[3],
                "dump": split[4],
                "fsck": split[5],
            }
        return d

    def get_mount(self, context, path):
        return self.get_all_active_mounts(context)[path]

    def apply(self, context, output):
        name = self.resource.name.as_string()

        self.check_path(context, name)

        try:
            self.get_mount(context, name)
            return

        except KeyError:
            command = ["mount"]

            fs_type = self.resource.fs_type.as_string()
            if fs_type:
                if fs_type == "bind":
                    command.append("--bind")
                else:
                    command.extend(("-t", fs_type))
            command.append(self.resource.device)
            command.append(self.resource.name)

            options = self.resource.options.resolve()
            if options:
                command.extend(("-o", options))

            context.change(ShellCommand(
                command=command,
                ))
            return True

