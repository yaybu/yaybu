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

    scm = String()
    """ The source control management system to use, e.g. subversion, git. """

    scm_username = String()
    """ The username for the remote repository """

    scm_password = String()
    """ The password for the remote repository. """

    user = String(default="root")
    """ The user to perform actions as, and who will own the resulting files. """


class CheckoutSyncPolicy(Policy):

    """ Synchronise the working copy with the remote SCM location. This is
    done by performing appropriate "switch" and "update" operations such that
    the working copy ends up in the correct state. This will never commit
    changes from the working copy - it is intended to track a remote location
    only. """

    resource = Checkout
    name = "sync"
    default = True
    signature = (
        Present("name"),
        Present("repository"),
        Present("branch"),
        )


class CheckoutExportPolicy(Policy):

    """ Perform an export of the remote location, as for example "svn export".
    This means this is not a working copy of the remote location, it is
    instead a clean copy of the specified source material. """

    resource = Checkout
    name = "export"
    default = False
    signature = (
        Present("name"),
        Present("repository"),
        Present("branch"),
        )

