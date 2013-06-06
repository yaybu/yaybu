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

import os
import logging
import urlparse
import urllib
import re

from yaybu.core.provider import Provider
from yaybu.core.error import CheckoutError, SystemError
from yaybu import resources
from yaybu.parts.provisioner.changes import ShellCommand, EnsureFile, EnsureDirectory


log = logging.getLogger(__name__)


hgrc = """
[paths]
default = %(repository)s
[extensions]
should = %(path)s/.hg/should.py
"""


def _inject_credentials(url, username=None, password=None):
    if username and password:
        p = urlparse.urlparse(url)
        netloc = '%s:%s@%s' % (
            urllib.quote(username, ''),
            urllib.quote(password, ''),
            p.hostname,
            )
        if p.port:
           netloc += ":" + str(p.port)
        url = urlparse.urlunparse((p.scheme,netloc,p.path,p.params,p.query,p.fragment))
    return url


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
        changed = False

        context.change(EnsureDirectory(self.resource.name, self.resource.user, self.resource.group, 0755))

        if not context.transport.exists(os.path.join(self.resource.name, ".hg")):
            try:
                self.action(context, "init")
            except SystemError:
                raise CheckoutError("Cannot initialise local repository.")
            created = True

        url = _inject_credentials(self.resource.repository, self.resource.scm_username, self.resource.scm_password)

        try:
            f = context.change(EnsureFile(
                os.path.join(self.resource.name, ".hg", "hgrc"),
                hgrc % {"repository": url, "path": self.resource.name},
                self.resource.user,
                self.resource.group,
                0600,
                True))
            changed = changed or f.changed
        except SystemError:
            raise CheckoutError("Could not set the remote repository.")

        try:
            f = context.change(EnsureFile(
                os.path.join(self.resource.name, ".hg", "should.py"),
                open(os.path.join(os.path.dirname(__file__), "mercurial.hgext")).read(),
                self.resource.user,
                self.resource.group,
                0600,
                True))
            changed = changed or f.changed
        except SystemError:
            raise CheckoutError("Could not setup mercurial idempotence extension")

        should_args = []
        if self.resource.branch:
            should_args.extend(["-b", self.resource.branch])
        if self.resource.tag:
            should_args.extend(["-t", self.resource.tag])

        if created or self.info(context, "should-pull", *should_args)[0] != 0:
            try:
                self.action(context, "pull", "--force")
                changed = True
            except SystemError:
                raise CheckoutError("Could not fetch changes from remote repository.")

        if created or self.info(context, "should-update", *should_args)[0] != 0:
            if self.resource.branch:
                args = [self.resource.branch]
            elif self.resource.tag:
                args = [self.resource.tag]
            else:
                args = []

            try:
                self.action(context, "update", *args)
                changed = True
            except SystemError:
                raise CheckoutError("Could not update working copy.")

        return created or changed

