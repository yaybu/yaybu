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
from yaybu.provisioner.changes import ShellCommand, EnsureFile
from yaybu.util import render_template


class File(provider.Provider):

    """ Provides file creation using templates or static files. """

    policies = (resources.file.FileApplyPolicy,)

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

    def get_file_contents(self, context):
        template = self.resource.template.as_string(default='')
        static = self.resource.static.as_string(default='')

        if template:
            template_args = self.resource.template_args.resolve()
            contents, sensitive = render_template(context, template, template_args)
            if template_args:
                 sensitive = sensitive or self.resource.template_args.contains_secrets()

        elif static:
            s = None
            fp = context.get_file(static)
            contents = fp.read()
            sensitive = "secret" in fp.labels

        else:
            contents = None
            sensitive = False

        return contents, sensitive

    def test(self, context):
        # Validate that the file exists and any template values can be filled in
        if self.resource.template.as_string():
            with context.root.ui.throbber("Testing '%s' exists and is a valid template..." % self.resource.template.as_string()):
                self.get_file_contents(context)
        elif self.resource.static.as_string():
            with context.root.ui.throbber("Testing '%s' exists..." % self.resource.static.as_string()):
                self.get_file_contents(context)

    def apply(self, context, output):
        name = self.resource.name.as_string()

        self.check_path(context, os.path.dirname(name), context.simulate)

        contents, sensitive = self.get_file_contents(context)

        fc = EnsureFile(
            name,
            contents,
            self.resource.owner.as_string(),
            self.resource.group.as_string(),
            self.resource.mode.resolve(),
            sensitive)
        context.change(fc)

        return fc.changed


class RemoveFile(provider.Provider):
    policies = (resources.file.FileRemovePolicy,)

    def apply(self, context, output):
        name = self.resource.name.as_string()
        if context.transport.exists(name):
            if not context.transport.isfile(name):
                raise error.InvalidProvider("%s exists and is not a file" % name)
            context.change(ShellCommand(["rm", self.resource.name]))
            changed = True
        else:
            context.changelog.debug("File %s missing already so not removed" % name)
            changed = False
        return changed


class WatchFile(provider.Provider):
    policies = (resources.file.FileWatchedPolicy, )

    def apply(self, context, output):
        """ Watched files don't have any policy applied to them """
        return self.resource.hash(context) != self.resource._original_hash

