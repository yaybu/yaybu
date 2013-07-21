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

from yaybu.provisioner.provider import Provider
from yaybu.core.error import CheckoutError, SystemError
from yaybu.provisioner import resources
from yaybu.provisioner.changes import ShellCommand, EnsureDirectory


log = logging.getLogger("git")

class Git(Provider):

    policies = (resources.checkout.CheckoutSyncPolicy,)

    REMOTE_NAME = "origin"

    @classmethod
    def isvalid(self, policy, resource, yay):
        scm = resource.scm.as_string(default='')
        return scm and scm.lower() == "git"

    def get_git_command(self, action, *args):
        command = [
            "git",
            #"--git-dir=%s" % os.path.join(self.resource.name, ".git"),
            #"--work-tree=%s" % self.resource.name,
            "--no-pager",
            action,
        ]

        command.extend(list(args))
        return command

    def info(self, context, action, *args):
        rc, stdout, stderr = context.transport.execute(
            self.get_git_command(action, *args),
            user=self.resource.user.as_string(),
            cwd=self.resource.name.as_string(),
            )
        return rc, stdout, stderr

    def action(self, context, action, *args):
        context.change(ShellCommand(
            self.get_git_command(action, *args),
            user=self.resource.user.as_string(),
            cwd=self.resource.name.as_string(),
            ))

    def action_clone(self, context):
        """Adds resource.repository as a remote, but unlike a
        typical clone, does not check it out

        """
        context.change(EnsureDirectory(self.resource.name.as_string(), self.resource.user.as_string(), self.resource.group.as_string(), 0755))

        try:
            self.action(context, "init", self.resource.name.as_string())
        except SystemError:
            raise CheckoutError("Cannot initialise local repository.")

        self.action_set_remote(context)

    def action_set_remote(self, context):
        try:
            self.action(context, "remote", "add", self.REMOTE_NAME, self.resource.repository.as_string())
        except SystemError:
            raise CheckoutError("Could not set the remote repository.")

    def action_update_remote(self, context):
        # Determine if the remote repository has changed
        remote_re = re.compile(self.REMOTE_NAME + r"\t(.*) \(.*\)\n")
        rv, stdout, stderr = self.info(context, "remote", "-v")
        remote = remote_re.search(stdout)
        if remote:
            if not self.resource.repository.as_string() == remote.group(1):
                log.info("The remote repository has changed.")
                try:
                    self.action(context, "remote", "rm", self.REMOTE_NAME)
                except SystemError:
                    raise CheckoutError("Could not delete remote '%s'" % self.REMOTE_NAME)
                self.action_set_remote(context)
                return True
        else:
            raise CheckoutError("Cannot determine repository remote.")

        return False

    def checkout_needed(self, context):
        # Determine which SHA is currently checked out.
        if context.transport.exists(os.path.join(self.resource.name.as_string(), ".git")):
            try:
                rv, stdout, stderr = self.info(context, "rev-parse", "--verify", "HEAD")
            except SystemError:
                head_sha = '0' * 40
            else:
                head_sha = stdout[:40]
                log.info("Current HEAD sha: %s" % head_sha)
        else:
            head_sha = '0' * 40

        try:
            rv, stdout, stderr = context.transport.execute(["git", "ls-remote", self.resource.repository.as_string()], cwd="/tmp")
        except SystemError:
            raise CheckoutError("Could not query the remote repository")

        r = re.compile('([0-9a-f]{40})\t(.*)\n')
        refs_to_shas = dict([(b,a) for (a,b) in r.findall(stdout)])

        # Revision takes precedent over branch

        revision = self.resource.revision.as_string()
        tag = self.resource.tag.as_string()
        branch = self.resource.branch.as_string()

        if revision:
            newref = revision
            if newref != head_sha:
                return newref

        elif tag:
            as_tag = "refs/tags/%s" % tag
            if not as_tag in refs_to_shas.keys():
                raise CheckoutError("Cannot find a tag called '%s'" % tag)

            annotated_tag = as_tag + "^{}"
            if annotated_tag in refs_to_shas.keys():
                as_tag = annotated_tag
            newref = tag
            if head_sha != refs_to_shas.get(as_tag):
                return newref

        elif branch:
            as_branch = "refs/heads/%s" % branch
            if not as_branch in refs_to_shas.keys():
                raise CheckoutError("Cannot find a branch called '%s'" % branch)
            newref = "remotes/%s/%s" % (
                self.REMOTE_NAME,
                branch
            )
            if head_sha != refs_to_shas.get(as_branch):
                return newref
        else:
            raise CheckoutError("You must specify either a revision, tag or branch")

    def action_checkout(self, context, newref):
        try:
            self.action(context, "fetch", self.REMOTE_NAME)
        except SystemError:
            raise CheckoutError("Could not fetch '%s'" % self.resource.repository.as_string())

        try:
            self.action(context, "checkout", newref)
        except SystemError:
            raise CheckoutError("Could not check out '%s'" % newref)

    def apply(self, context, output):
        # If necessary, clone the repository
        if not context.transport.exists(os.path.join(self.resource.name.as_string(), ".git")):
            self.action_clone(context)
            changed = True
        else:
            changed = self.action_update_remote(context)

        newref = self.checkout_needed(context)
        if newref:
            self.action_checkout(context, newref)

        return changed or newref

