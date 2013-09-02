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
from yaybu.provisioner.changes import EnsureDirectory, ShellCommand


class Directory(provider.Provider):

    policies = (resources.directory.DirectoryAppliedPolicy,)

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

    def apply(self, context, output):
        name = self.resource.name.as_string()

        changed = False
        self.check_path(context, os.path.dirname(name))

        return context.change(EnsureDirectory(
            name,
            self.resource.owner.as_string(),
            self.resource.group.as_string(),
            self.resource.mode.resolve(),
            self.resource.parents.resolve(),
            ))


class RemoveDirectory(provider.Provider):

    policies = (resources.directory.DirectoryRemovedPolicy,)

    def apply(self, context, output):
        name = self.resource.name.as_string()

        if context.transport.exists(name) and not context.transport.isdir(name):
            raise error.InvalidProviderError("%r: %s exists and is not a directory" % (self, name))
        if context.transport.exists(name):
            context.change(ShellCommand(["/bin/rmdir", self.resource.name]))
            changed = True
        else:
            changed = False
        return changed


class RemoveDirectoryRecursive(provider.Provider):

    policies = (resources.directory.DirectoryRemovedRecursivePolicy,)

    def apply(self, context, output):
        name = self.resource.name.as_string()

        if context.transport.exists(name) and not context.transport.isdir(name):
            raise error.InvalidProviderError("%r: %s exists and is not a directory" % (self, name))
        if context.transport.exists(name):
            context.change(ShellCommand(["/bin/rm", "-rf", self.resource.name]))
            changed = True
        else:
            changed = False
        return changed

