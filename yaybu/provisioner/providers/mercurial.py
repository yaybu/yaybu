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

from yaybu.provisioner.provider import Provider
from yaybu.core.error import CheckoutError, SystemError
from yaybu.provisioner import resources
from yaybu.provisioner.changes import ShellCommand, EnsureFile, EnsureDirectory


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
        scm = resource.scm.as_string(default='')
        return scm and scm.lower() == "mercurial"

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
            user=self.resource.user.as_string(),
            cwd=self.resource.name.as_string(),
            )
        return rc, stdout, stderr

    def action(self, context, action, *args):
        context.change(ShellCommand(
            self.get_hg_command(action, *args),
            user=self.resource.user.as_string(),
            cwd=self.resource.name.as_string(),
            ))

    def apply(self, context, output):
        created = False
        changed = False

        context.change(EnsureDirectory(self.resource.name.as_string(), self.resource.user.as_string(), self.resource.group.as_string(), 0755))

        if not context.transport.exists(os.path.join(self.resource.name.as_string(), ".hg")):
            try:
                self.action(context, "init")
            except SystemError:
                raise CheckoutError("Cannot initialise local repository.")
            created = True

        url = _inject_credentials(self.resource.repository.as_string(), self.resource.scm_username.as_string(), self.resource.scm_password.as_string())

        try:
            f = context.change(EnsureFile(
                os.path.join(self.resource.name.as_string(), ".hg", "hgrc"),
                hgrc % {"repository": url, "path": self.resource.name.as_string()},
                self.resource.user.as_string(),
                self.resource.group.as_string(),
                0600,
                True))
            # changed = changed or f.changed
        except SystemError:
            raise CheckoutError("Could not set the remote repository.")

        try:
            f = context.change(EnsureFile(
                os.path.join(self.resource.name.as_string(), ".hg", "should.py"),
                open(os.path.join(os.path.dirname(__file__), "mercurial.hgext")).read(),
                self.resource.user.as_string(),
                self.resource.group.as_string(),
                0600,
                True))
            # changed = changed or f.changed
        except SystemError:
            raise CheckoutError("Could not setup mercurial idempotence extension")

        should_args = []
        if self.resource.branch.as_string(default=''):
            should_args.extend(["-b", self.resource.branch.as_string()])
        if self.resource.tag.as_string(default=''):
            should_args.extend(["-t", self.resource.tag.as_string()])

        if created or self.info(context, "should-pull", *should_args)[0] != 0:
            try:
                self.action(context, "pull", "--force")
                changed = True
            except SystemError:
                raise CheckoutError("Could not fetch changes from remote repository.")

        if created or self.info(context, "should-update", *should_args)[0] != 0:
            if self.resource.tag.as_string():
                args = [self.resource.tag]
            elif self.resource.branch.as_string():
                args = [self.resource.branch]
            else:
                args = []

            try:
                self.action(context, "update", *args)
                changed = True
            except SystemError:
                raise CheckoutError("Could not update working copy.")

        return created or changed

