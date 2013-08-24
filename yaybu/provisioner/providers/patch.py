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

from jinja2 import Environment, BaseLoader, TemplateNotFound

from yaybu import error
from yaybu.provisioner import resources
from yaybu.provisioner import provider
from yaybu.provisioner.changes import EnsureFile
import subprocess

from yay import String


class YaybuTemplateLoader(BaseLoader):

    def __init__(self, ctx):
        self.ctx = ctx
        self.secret = False

    def get_source(self, environment, template):
        f = self.ctx.get_file(template)
        source = f.read()
        self.secret = self.secret or "secret" in f.labels
        return source, template, lambda: False


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

        cmd = 'patch --dry-run -N --silent -r - -o - %s -' % self.resource.source.as_string()
        returncode, stdout, stderr = context.transport.execute(cmd, stdin=patch)

        if returncode != 0:
            raise error.CommandError("Unable to apply patch\n" + stderr)

        return stdout, sensitive

    def apply(self, context, output):
        name = self.resource.name.as_string()

        self.check_path(context, os.path.dirname(name), context.simulate)

        contents, sensitive = self.apply_patch(context)

        template_args = self.resource.template_args.resolve()
        if template_args:
            loader = YaybuTemplateLoader(context)
            env = Environment(loader=loader, line_statement_prefix='%')
            template = env.from_string(contents)
            contents = template.render(template_args)
            sensitive = loader.secret or self.resource.template_args.contains_secrets()

        fc = EnsureFile(name, contents, self.resource.owner.as_string(), self.resource.group.as_string(), self.resource.mode.resolve(), sensitive)
        context.change(fc)

        return fc.changed
