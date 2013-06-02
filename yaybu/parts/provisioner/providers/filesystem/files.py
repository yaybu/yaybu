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

from yaybu import resources
from yaybu.core import error, provider
from yaybu.parts.provisioner.changes import ShellCommand, AttributeChanger, EnsureFile

from yay import String


class YaybuTemplateLoader(BaseLoader):

    def __init__(self, ctx):
        self.ctx = ctx

    def get_source(self, environment, template):
        f = self.ctx.get_file(template)
        source = f.read()
        return source, template, lambda: False


class File(provider.Provider):

    """ Provides file creation using templates or static files. """

    policies = (resources.file.FileApplyPolicy,)

    @classmethod
    def isvalid(self, *args, **kwargs):
        return super(File, self).isvalid(*args, **kwargs)

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

    def get_file_contents(self, context):
        if self.resource.template:
            # set a special line ending
            # this strips the \n from the template line meaning no blank line,
            # if a template variable is undefined. See ./yaybu/recipe/interfaces.j2 for an example
            env = Environment(loader=YaybuTemplateLoader(context), line_statement_prefix='%')
            template = env.get_template(self.resource.template)
            contents = template.render(self.get_template_args()) + "\n" # yuk
            sensitive = self.has_protected_strings()

        elif self.resource.static:
            s = None
            fp = context.get_file(self.resource.static)
            contents = fp.read()

            sensitive = getattr(fp, 'secret', False)

        else:
            contents = None
            sensitive = False

        return contents, sensitive

    def test(self, context):
        # Validate that the file exists and any template values can be filled in
        if self.resource.template:
            print "Testing '%s' exists and is a valid Jinja2 template" % self.resource.template
            self.get_file_contents(context)
        elif self.resource.static:
            print "Testing '%s' exists" % self.resource.static
            self.get_file_contents(context)

    def apply(self, context):
        name = self.resource.name

        self.check_path(context, os.path.dirname(name), context.simulate)

        contents, sensitive = self.get_file_contents(context)

        fc = EnsureFile(self.resource.name, contents, self.resource.owner, self.resource.group, self.resource.mode, sensitive)
        context.change(fc)

        return fc.changed


class RemoveFile(provider.Provider):
    policies = (resources.file.FileRemovePolicy,)

    @classmethod
    def isvalid(self, *args, **kwargs):
        return super(RemoveFile, self).isvalid(*args, **kwargs)

    def apply(self, context):
        if context.transport.exists(self.resource.name):
            if not context.transport.isfile(self.resource.name):
                raise error.InvalidProvider("%s exists and is not a file" % self.resource.name)
            context.change(ShellCommand(["rm", self.resource.name]))
            changed = True
        else:
            context.changelog.debug("File %s missing already so not removed" % self.resource.name)
            changed = False
        return changed


class WatchFile(provider.Provider):
    policies = (resources.file.FileWatchedPolicy, )

    @classmethod
    def isvalid(self, *args, **kwargs):
        return super(WatchFile, self).isvalid(*args, **kwargs)

    def apply(self, context):
        """ Watched files don't have any policy applied to them """
        return self.resource.hash(context) != self.resource._original_hash

