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
import logging

from yaybu import error
from yaybu.provisioner import resources
from yaybu.provisioner import provider
from yaybu.provisioner.changes import EnsureDirectory, ShellCommand


class Directory(provider.Provider):

    policies = (resources.directory.DirectoryAppliedPolicy,)

    @classmethod
    def isvalid(self, *args, **kwargs):
        return super(Directory, self).isvalid(*args, **kwargs)

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
                if self.resource.parents:
                    return
                if simulate:
                    return
                raise error.PathComponentMissing(path)
            if not transport.isdir(path):
                raise error.PathComponentNotDirectory(path)

    def apply(self, context):
        changed = False
        self.check_path(context, os.path.dirname(self.resource.name))

        return context.change(EnsureDirectory(
            self.resource.name,
            self.resource.owner,
            self.resource.group,
            self.resource.mode,
            self.resource.parents,
            ))


class RemoveDirectory(provider.Provider):

    policies = (resources.directory.DirectoryRemovedPolicy,)

    @classmethod
    def isvalid(self, *args, **kwargs):
        return super(RemoveDirectory, self).isvalid(*args, **kwargs)

    def apply(self, context):
        if context.transport.exists(self.resource.name) and not context.transport.isdir(self.resource.name):
            raise error.InvalidProviderError("%r: %s exists and is not a directory" % (self, self.resource.name))
        if context.transport.exists(self.resource.name):
            context.change(ShellCommand(["/bin/rmdir", self.resource.name]))
            changed = True
        else:
            changed = False
        return changed


class RemoveDirectoryRecursive(provider.Provider):

    policies = (resources.directory.DirectoryRemovedRecursivePolicy,)

    @classmethod
    def isvalid(self, *args, **kwargs):
        return super(RemoveDirectoryRecursive, self).isvalid(*args, **kwargs)

    def apply(self, context):
        if context.transport.exists(self.resource.name) and not context.transport.isdir(self.resource.name):
            raise error.InvalidProviderError("%r: %s exists and is not a directory" % (self, self.resource.name))
        if context.transport.exists(self.resource.name):
            context.change(ShellCommand(["/bin/rm", "-rf", self.resource.name]))
            changed = True
        else:
            changed = False
        return changed

