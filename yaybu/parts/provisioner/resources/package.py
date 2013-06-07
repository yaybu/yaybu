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

from yaybu.core.resource import Resource
from yaybu.core.policy import (
    Policy,
    Absent,
    Present,
    )
from yaybu.core.argument import (
    String,
    File,
    Boolean,
    )


class Package(Resource):

    """ Represents an operating system package, installed and managed via the
    OS package management system. For example, to ensure these three packages
    are installed::

        Package:
            - name: apache2
            - name: zip
            - name: xsltproc

    """

    name = String()
    """ The name of the package. This can be a single package or a list can be
    supplied. """

    version = String()
    """ The version of the package, if only a single package is specified and
    the appropriate provider supports it (the Apt provider does not support
    it). """

    purge = Boolean(default=False)
    """ When removing a package, whether to purge it or not. """

class PackageInstallPolicy(Policy):

    """ Install the specified package. If the package is already installed it
    will not be upgraded or changed. Your package upgrade and patching
    strategy should be independent of Yaybu in general.
    """

    resource = Package
    name = "install"
    default = True
    signature = (
        Present("name"),
        Absent("purge"),
        )

class PackageUninstallPolicy(Policy):

    """ Uninstall the specified package, if it is installed. """

    resource = Package
    name = "uninstall"
    default = False
    signature = (
        Present("name"),
        Absent("version"),
        )

