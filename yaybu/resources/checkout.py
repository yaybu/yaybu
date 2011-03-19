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
from yaybu.core.policy import Policy
from yaybu.core.argument import (
    FullPath,
    String,
    Octal,
    )

class Checkout(Resource):
    """ This represents a "working copy" from a Source Code Management system.
    This could be provided by, for example, Subversion or Git remote
    repositories.

    Note that this is '*a* checkout', not 'to checkout'. This represents the
    resource itself on disk. If you change the details of the working copy
    (for example changing the branch) the provider will execute appropriate
    commands (such as `svn switch`) to take the resource to the desired state.
    """

    name = FullPath()
    """ The full path to the working copy on disk. """

    repository = String()
    """ The identifier for the repository - this could be an http url for
    subversion or a git url for git, for example. """

    branch = String()
    """ The name of a branch to check out, if required. """

    revision = String()
    """ The revision to check out or move to. """

    scm_username = String()
    """ The username for the remote repository """

    scm_password = String()
    """ The password for the remote repository. """

    user = String(default="root")
    """ The user to perform actions as, and who will own the resulting files. """


class CheckoutSyncPolicy(Policy):

    resource = Checkout
    name = "sync"
    default = True


class CheckoutExportPolicy(Policy):

    resource = Checkout
    name = "export"
    default = False
