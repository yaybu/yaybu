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
from yaybu.core.error import CheckoutError
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
            #"--git-dir=%s" % os.path.join(self.resource.name, ".git"),
            #"--work-tree=%s" % self.resource.name,
            "--no-pager",
            action,
        ]

        command.extend(list(args))

        if os.path.exists(self.resource.name):
            cwd = self.resource.name
        else:
            cwd = os.path.dirname(self.resource.name)

        return context.shell.execute(command, user=self.resource.user, exceptions=False, cwd=cwd, **kwargs)

    def action_clone(self, context):
        """Adds resource.repository as a remote, but unlike a
        typical clone, does not check it out

        """
        if not os.path.exists(self.resource.name):
            rv, out, err = context.shell.execute(
                ["/bin/mkdir", self.resource.name],
                user=self.resource.user,
                exceptions=False,
            )

            if not rv == 0:
                raise CheckoutError("Cannot create the repository directory")

            rv, out, err = self.git(context, "init", self.resource.name)
            if not rv == 0:
                raise CheckoutError("Cannot initialise local repository.")

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

        rv, out, err = self.git(context, *git_parameters)

        if not rv == 0:
            raise CheckoutError("Could not set the remote repository.")

    def action_update_remote(self, context):
        # Determine if the remote repository has changed
        remote_re = re.compile(self.REMOTE_NAME + r"\t(.*) \(.*\)\n")
        rv, stdout, stderr = self.git(context, "remote", "-v", passthru=True)
        remote = remote_re.search(stdout)
        if remote:
            if not self.resource.repository == remote.group(1):
                log.info("The remote repository has changed.")
                self.git(context, "remote", "rm", self.REMOTE_NAME)
                self.action_set_remote(context)
                return True
        else:
            raise CheckoutError("Cannot determine repository remote.")

        return False

    def action_checkout(self, context):
        # Determine which SHA is currently checked out.
        if os.path.exists(os.path.join(self.resource.name, ".git")):
            rv, stdout, stderr = self.git(context, "rev-parse", "--verify", "HEAD", passthru=True)
            if not rv == 0:
                head_sha = '0' * 40
            else:
                head_sha = stdout[:40]
                log.info("Current HEAD sha: %s" % head_sha)
        else:
            head_sha = '0' * 40

        changed = True
        # Revision takes precedent over branch
        if self.resource.revision:
            newref = self.resource.revision
            if newref == head_sha:
                changed = False
        elif self.resource.branch:
            rv, stdout, stderr = self.git(context, "ls-remote",
                                        self.resource.repository, passthru=True)
            if not rv == 0:
                raise CheckoutError("Could not query the remote repository")
            r = re.compile('([0-9a-f]{40})\t(.*)\n')
            refs_to_shas = dict([(b,a) for (a,b) in r.findall(stdout)])

            as_tag = "refs/tags/%s" % self.resource.branch
            as_branch = "refs/heads/%s" % self.resource.branch

            if as_tag in refs_to_shas.keys():
                annotated_tag = as_tag + "^{}"
                if annotated_tag in refs_to_shas.keys():
                    as_tag = annotated_tag
                newref = self.resource.branch
                changed = head_sha != refs_to_shas.get(as_tag)
            elif as_branch in refs_to_shas.keys():
                newref = "remotes/%s/%s" % (
                    self.REMOTE_NAME,
                    self.resource.branch
                )
                changed = head_sha != refs_to_shas.get(as_branch)
        else:
            raise CheckoutError("You must specify either a revision or a branch")

        if changed:
            rv, stdout, stderr = self.git(context, "checkout", newref)
            if not rv == 0:
                raise CheckoutError("Could not check out '%s'" % newref)

        return changed

    def apply(self, context):
        log.info("Syncing %s" % self.resource)

        # If necessary, clone the repository
        if not os.path.exists(os.path.join(self.resource.name, ".git")):
            self.action_clone(context)
        else:
            self.action_update_remote(context)

        # Always update the REMOTE_NAME remote
        self.git(context, "fetch", self.REMOTE_NAME)

        return self.action_checkout(context)
