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

import os, logging
import re

from yaybu.core.provider import Provider
from yaybu import resources

log = logging.getLogger("git")

class Git(Provider):

    policies = (resources.checkout.CheckoutSyncPolicy,)

    REMOTE_NAME = "origin"

    @classmethod
    def isvalid(self, policy, resource, yay):
        return resource.scm and resource.scm.lower() == "git"

    def git(self, context, action, *args, **kwargs):
        command = [
            "git",
            "--git-dir=%s" % os.path.join(self.resource.name, ".git"),
            "--work-tree=%s" % self.resource.name,
            "--no-pager",
            action,
        ]

        command.extend(list(args))

        return context.shell.execute(command, user=self.resource.user)

    def action_clone(self, context):
        """Adds resource.repository as a remote, but unlike a
        typical clone, does not check it out

        """
        if not os.path.exists(os.path.join(self.resource.name, ".git")):
            self.git(context, "init", self.resource.name)
            self.action_set_remote(context)
            return True
        else:
            return False

    def action_set_remote(self, context):
        git_parameters = [
            "remote", "add",
            self.REMOTE_NAME,
            self.resource.repository,
        ]

        # If necessary, only fetch the branch we need
        if self.resource.branch:
            git_parameters.extend([
                "-t", self.resource.branch,
                "-m", self.resource.branch,
            ])

        self.git(context, *git_parameters)

    def action_checkout(self, context):
        # Revision takes precedent over branch
        if self.resource.revision:
            newref = self.resource.revision
        elif self.resource.branch:
            newref = "%s/%s" % (self.REMOTE_NAME, self.resource.branch)
        else:
            raise CheckoutError("You must specify either a revision or a branch")

        # check to see if anything has changed
        returncode, stdout, stderr = self.git(context, "diff", "--shortstat", newref)
        if stdout.strip() == "":
            return False
        else:
            self.git(context, "checkout", newref)
            return True

    def apply(self, context):
        log.info("Syncing %s" % self.resource)

        # If necessary, clone the repository
        if not os.path.exists(os.path.join(self.resource.name, ".git")):
            self.action_clone(context)

        # Determine if the remote repository has changed
        remote_re = re.compile(self.REMOTE_NAME + r"\t(.*) \(.*\)\n")
        returncode, stdout, stderr = self.git(context, "remote", "-v")
        remote = remote_re.search(stdout)
        if remote:
            if not self.resource.repository == remote.group(1):
                log.info("The remote repository has changed.")
                self.git(context, "remote", "rm", self.REMOTE_NAME)
                self.action_set_remote(context)

        # Always update the remotes
        self.git(context, "remote", "update")

        return self.action_checkout(context)
