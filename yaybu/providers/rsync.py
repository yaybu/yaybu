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

from yaybu.providers.filesystem.files import AttributeChanger


class Rsync(Provider):

    policies = (resources.checkout.CheckoutSyncPolicy,)

    REMOTE_NAME = "origin"

    @classmethod
    def isvalid(self, policy, resource, yay):
        return resource.scm and resource.scm.lower() == "rsync"

    def _get_svn_ignore(self, context, path):
        command = ["svn", "status", "--non-interactive", "--no-ignore", path]
        returncode, stdout, stderr = context.shell.execute(command, passthru=True)

        if not returncode == 0:
            raise CheckoutError("Could not generate updated .rsync-exclude for Subversion checkout")

        ignore = []
        for line in stdout.split("\n"):
            if not line.startswith("I"):
                continue
            ignore.append(os.path.relpath(line.lstrip("I").strip(), start=path))

        return ignore

    def _build_exclude_list(self, context):
        path = os.path.join(self.resource.name, ".rsync-exclude")

        ignore = [".rsync-exclude"]

        if os.path.isdir(self.resource.repository):
            svndir = os.path.join(self.resource.repository, ".svn")
            if os.path.isdir(svndir):
                ignore.append(".svn")
                ignore.extend(self._get_svn_ignore(context, self.resource.repository))

            #gitdir = os.path.join(self.resource.repository, ".git")
            #if os.path.isdir(gitdir):
            #    ignore.extend(self._get_git_ignore(context, self.resource.repository))

            ignorefile = os.path.join(self.resource.repository, ".rsync-exclude")
            if os.path.exists(ignorefile):
                ignore.extend(x for x in open(ignorefile).read().split("\n") if x.strip())

        open(path, "w").write("\n".join(ignore))

        return path

    def _sync(self, context, dryrun=False):
        # FIXME: This will touch disk even in simulate mode... But *only* the exclude file.
        command = ["rsync", "-rltv", "--stats", "--delete", "--exclude-from", self._build_exclude_list(context)]
        if dryrun:
            command.extend(["-n"])
        command.extend([".", self.resource.name+"/"])

        rv, out, err = context.shell.execute(command, cwd=self.resource.repository, user=self.resource.user, exceptions=False, passthru=dryrun)

        if not "Number of files transferred: 0" in out:
            return True

        return False

    def apply(self, context):
        changed = False

        if not os.path.exists(self.resource.name):
            command = ["/bin/mkdir", self.resource.name]
            rv, out, err = context.shell.execute(command, exceptions=False)
            changed = True

        ac = AttributeChanger(context, self.resource.name, self.resource.user, mode=0755)
        ac.apply(context)
        changed = changed or ac.changed

        if self._sync(context, True):
            self._sync(context)
            changed = True

        return changed

