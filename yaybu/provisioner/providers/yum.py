# Copyright 2013 Isotoma Limited
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
from yaybu import error
from yaybu.provisioner import resources
from yaybu.provisioner.changes import ShellCommand


def is_installed(context, resource):
    command = ['rpm', '-q', resource.name.as_string()]
    rc, stdout, stderr = context.transport.execute(command)
    if rc == 1:
        return False
    if rc == 0:
        return True
    # if the return code is anything but zero or one, we have a problem
    raise error.RpmError(
        "%s search failed with return code %s" % (resource, rc))


class YumInstall(provider.Provider):

    policies = (resources.package.PackageInstallPolicy,)

    @classmethod
    def isvalid(self, policy, resource, context):
        return context.transport.exists("/usr/bin/rpm")

    def apply(self, context, output):
        if is_installed(context, self.resource):
            return False

        command = ["yum", "install", "-y", self.resource.name.as_string()]

        try:
            context.change(ShellCommand(command))
        except error.SystemError as exc:
            raise error.YumError(
                "%s failed with return code %d" %
                (self.resource, exc.returncode))

        return True


class YumUninstall(provider.Provider):

    policies = (resources.package.PackageUninstallPolicy,)

    @classmethod
    def isvalid(self, policy, resource, context):
        return context.transport.exists("/usr/bin/rpm")

    def apply(self, context, output):
        if not is_installed(context, self.resource):
            return False

        command = ["yum", "remove", "-y", self.resource.name.as_string()]

        try:
            context.change(ShellCommand(command))
        except error.SystemError as exc:
            raise error.YumError(
                "%s failed to uninstall with return code %d" % (self.resource, exc.returncode))

        return True
