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

import os, logging
import re

from yaybu.core.provider import Provider
from yaybu.core.error import CheckoutError, SystemError
from yaybu import resources
from yaybu.parts.provisioner.changes import File, ShellCommand, EnsureDirectory


log = logging.getLogger(__name__)


hgrc = """
[paths]
default = %(remote)s
[extensions]
should = %(path)s/.hg/should.py
"""


class Mercurial(Provider):

    policies = (resources.checkout.CheckoutSyncPolicy,)

    @classmethod
    def isvalid(self, policy, resource, yay):
        return resource.scm and resource.scm.lower() == "mercurial"

    def get_hg_command(self, action, *args):
        command = [
            "hg",
            action,
        ]

        command.extend(list(args))
        return command

    def info(self, context, action, *args):
        rc, stdout, stderr = context.transport.execute(
            self.get_hg_command(action, *args),
            user=self.resource.user,
            cwd=self.resource.name,
            )
        return rc, stdout, stderr

    def action(self, context, action, *args):
        context.change(ShellCommand(
            self.get_hg_command(action, *args),
            user=self.resource.user,
            cwd=self.resource.name,
            ))

    def apply(self, context):
        created = False

        context.change(EnsureDirectory(self.resource.name, self.resource.user, self.resource.group, 0755))

        if not context.transport.exists(os.path.join(self.resource.name, ".hg")):
            try:
                self.action(context, "init")
            except SystemError:
                raise CheckoutError("Cannot initialise local repository.")
            created = True

        try:
            context.change(FileContentChanger(
                os.path.join(self.resource.name, ".hg", "hgrc"),
                0600,
                hgrc % {"repository": self.resource.repository, "path": self.resource.name},
                True))
        except SystemError:
            raise CheckoutError("Could not set the remote repository.")

        try:
            context.change(FileContentChanger(
                os.path.join(self.resource.name, ".hg", "should.py"),
                0600,
                open(os.path.join(os.path.dirname(__file__), "mercurial.hgext")).read(),
                True))
        except SystemError:
            raise CheckoutError("Could not setup mercurial idempotence extension")

        if created or self.info(context, "should-pull"):
            try:
                self.action(context, "pull", "--force")
            except SystemError:
                raise CheckoutError("Could not fetch changes from remote repository.")

        if created or self.info(context, "should-update"):
            try:
                self.action(context, "update")
            except SystemError:
                raise CheckoutError("Could not update working copy.")

        return True

