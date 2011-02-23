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

from yaybu.core import provider
from yaybu.core import error
from yaybu import resources

class Apt(provider.Provider):

    policies = (resources.package.PackageInstallPolicy,)

    @classmethod
    def isvalid(self, *args, **kwargs):
        return super(Apt, self).isvalid(*args, **kwargs)

    def apply(self, shell):

        # work out if the package is already installed
        command = ["dpkg", "-s", self.resource.name]
        returncode, stdout, stderr = shell.execute(command, exceptions=False, passthru=True)

        # if the return code is 0, the package is installed
        if returncode == 0:
            return False

        # if the return code is 1, it is not installed, if it's anything else, we have a problem
        if returncode > 1:
            raise error.DpkgError("%s search failed with return code %s" % (self.resource, returncode))


        # the search returned 1, package is not installed, continue and install it
        command = ["apt-get", "install", "-q", "-y", self.resource.name]
        returncode, stdout, stderr = shell.execute(command)

        if returncode != 0:
            raise error.AptError("%s failed with return code %d" % (self.resource, returncode))

        return True

