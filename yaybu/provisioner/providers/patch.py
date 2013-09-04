# Copyright 2011-2013 Isotoma Limited
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

from yaybu import error
from yaybu.provisioner import resources
from yaybu.provisioner import provider
from yaybu.provisioner.changes import EnsureFile
from yaybu.util import render_string


class Patch(provider.Provider):

    """ Provides file creation using templates or static files. """

    policies = (resources.patch.PatchApplyPolicy,)

    def check_path(self, ctx, directory, simulate):
        if ctx.transport.isdir(directory):
            return
        frags = directory.split("/")
        path = "/"
        for i in frags:
            path = os.path.join(path, i)
            if not ctx.transport.exists(path): #FIXME
                if not simulate:
                    raise error.PathComponentMissing(path)
            elif not ctx.transport.isdir(path):
                raise error.PathComponentNotDirectory(path)

    def get_patch(self, context):
        patch = context.get_file(self.resource.patch.as_string())
        data = patch.read()
        #FIXME: Would be good to validate the patch here a bit
        return data, "secret" in patch.labels

    def apply_patch(self, context):
        patch, sensitive = self.get_patch(context)

        cmd = 'patch -t --dry-run -N --silent -r - -o - %s -' % self.resource.source.as_string()
        returncode, stdout, stderr = context.transport.execute(cmd, stdin=patch)

        if returncode != 0:
            context.changelog.info("Patch does not apply cleanly")
            context.changelog.info("Patch file used was %s" % self.resource.patch.as_string())
            context.changelog.info("File to patch was %s" % self.resource.source.as_string())

            context.changelog.info("")
            context.changelog.info("Reported error was:")
            map(context.changelog.info, stderr.split("\n"))

            raise error.CommandError("Unable to apply patch")

        return stdout, sensitive

    def test(self, context):
        # Validate that the file exists and any template values can be filled in
        with context.root.ui.throbber("Testing '%s' exists..." % self.resource.patch.as_string()):
            self.get_patch(context)

    def apply(self, context, output):
        name = self.resource.name.as_string()

        self.check_path(context, os.path.dirname(name), context.simulate)

        contents, sensitive = self.apply_patch(context)

        template_args = self.resource.template_args.resolve()
        if template_args:
            contents, secret = render_string(context, contents, template_args)
            sensitive = sensitive or secret

        fc = EnsureFile(name, contents, self.resource.owner.as_string(), self.resource.group.as_string(), self.resource.mode.resolve(), sensitive)
        context.change(fc)

        return fc.changed
