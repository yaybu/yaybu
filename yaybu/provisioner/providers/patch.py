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

    def get_source(self, environment, template):
        f = self.ctx.get_file(template)
        source = f.read()
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

    def has_protected_strings(self):
        def iter(val):
            if isinstance(val, dict):
                for v in val.values():
                    if iter(v):
                        return True
                return False

            elif isinstance(val, list):
                for v in val:
                    if iter(v):
                        return True
                return False

            else:
                return isinstance(val, String)

        return iter(self.resource.template_args)

    def get_template_args(self):
        """ I return a copy of the template_args that contains only basic types (i.e. no protected strings) """
        def _(val):
            if isinstance(val, dict):
                return dict((k,_(v)) for (k,v) in val.items())
            elif isinstance(val, list):
                return list(_(v) for v in val)
            elif isinstance(val, String):
                return val.unprotected
            else:
                return val
        return _(self.resource.template_args)

    def get_patch(self, context):
        patch = context.get_file(self.resource.patch).read()

        #FIXME: Would be good to validate the patch here a bit

        return patch

    def apply_patch(self, context):
        cmd = 'patch --dry-run -p%d -N --silent -r - -o - %s -' % (self.resource.strip, self.resource.source)
        returncode, stdout, stderr = context.transport.execute(cmd, stdin=self.get_patch(context))

        if returncode != 0:
            raise error.CommandError("Unable to apply patch\n" + stderr)

        return stdout

    def apply(self, context, output):
        name = self.resource.name
        self.check_path(context, os.path.dirname(name), context.simulate)

        contents = self.apply_patch(context)

        sensitive = False

        if self.resource.template_args:
            env = Environment(loader=YaybuTemplateLoader(context), line_statement_prefix='%')
            template = env.from_string(contents)
            contents = template.render(self.get_template_args()) #+ "\n" # yuk
            sensitive = self.has_protected_strings()

        fc = EnsureFile(name, contents, self.resource.owner, self.resource.group, self.resource.mode, sensitive)
        context.change(fc)

        return fc.changed

