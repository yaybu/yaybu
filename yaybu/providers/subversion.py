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

from yaybu.core.shell import Command
from yaybu.core.provider import Provider
from yaybu.core.error import MissingDependency
from yaybu import resources

import shlex


log = logging.getLogger("subversion")

class Svn(Provider):

    policies = (resources.checkout.CheckoutSyncPolicy,)

    @classmethod
    def isvalid(self, policy, resource, yay):
        identities = [
            'svn',
            'subversion',
        ]

        if resource.scm:
            return resource.scm.lower() in identities

        # TODO: ensure that this should be made default provider
        return True

    @property
    def url(self):
        return self.resource.repository + "/" + self.resource.branch

    def action_checkout(self, context):
        if os.path.exists(self.resource.name):
            return

        log.debug("Checking out %s" % self.resource)
        self.svn(context, "co", self.url, self.resource.name)
        return True

    def apply(self, context):
        if not os.path.exists("/usr/bin/svn"):
            error_string = "'/usr/bin/svn' is not available; update your configuration to install subversion?"
            if not context.simulate:
                raise MissingDependency(error_string)
            log.info(error_string)
            log.info("This error was ignored in simulate mode")

        if not os.path.exists(self.resource.name):
            return self.action_checkout(context)

        log.debug("Syncing %s" % self.resource)

        changed = False

        info = self.info(context, self.resource.name)
        repo_info = self.info(context, self.url)

        # If the 'Repository Root' is different between the checkout and the repo, switch --relocated
        old_repo_root = info["Repository Root"]
        new_repo_root = repo_info["Repository Root"]
        if old_repo_root != new_repo_root:
            log.info("Switching repository root from '%s' to '%s'" % (old_repo_root, new_repo_root))
            self.svn(context, "switch", "--relocate", old_repo_root, new_repo_root, self.resource.name)
            changed = True

        # If we have changed branch, switch
        old_url = info["URL"]
        new_url = repo_info["URL"]
        if old_url != new_url:
            log.info("Switching branch from '%s' to '%s'" % (old_url, new_url))
            self.svn(context, "switch", new_url, self.resource.name)
            changed = True

        # If we have changed revision, svn up
        # FIXME: Eventually we might want revision to be specified in the resource?
        current_rev = info["Last Changed Rev"]
        target_rev = repo_info["Last Changed Rev"]
        if current_rev != target_rev:
            log.info("Switching revision from %s to %s" % (current_rev, target_rev))
            self.svn(context, "up", "-r", target_rev, self.resource.name)
            changed = True

        return changed

    def action_export(self, context):
        if os.path.exists(self.resource.name):
            return
        log.debug("Exporting %s" % self.resource)
        self.svn(context, "export", self.url, self.resource.name)

    def get_svn_args(self, action, *args, **kwargs):
        command = Command(["svn"])

        if kwargs.get("quiet", False):
            command.add("--quiet")

        command.extend([action, "--non-interactive"])

        if self.resource.scm_username:
            command.add(Command(["--username", self.resource.scm_username]))
        if self.resource.scm_password:
            command.add(Command(["--password", self.resource.scm_password]))
        if self.resource.scm_username or self.resource.scm_password:
            command.add("--no-auth-cache")

        for arg in args:
            command.add(arg)

        return command

    def info(self, context, uri):
        command = self.get_svn_args("info", uri)
        returncode, stdout, stderr = context.shell.execute(command, passthru=True)
        return dict(x.split(": ") for x in stdout.split("\n") if x)

    def svn(self, context, action, *args, **kwargs):
        command = self.get_svn_args(action, *args, **kwargs)
        return context.shell.execute(command, user=self.resource.user)


