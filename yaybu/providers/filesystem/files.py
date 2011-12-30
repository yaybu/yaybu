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

import os
import sys
import stat
import pwd
import grp
import difflib
import logging
import string

try:
    import magic
except ImportError:
    magic = None

from jinja2 import Environment, BaseLoader, TemplateNotFound

from yaybu import resources
from yaybu.core import provider
from yaybu.core import change
from yaybu.core import error

from yay import String


def binary_buffers(*buffers):

    """ Check all of the passed buffers to see if any of them are binary. If
    any of them are binary this will return True. """
    if not magic:
        check = lambda buff: len(buff) == sum(1 for c in buff if c in string.printable)
    else:
        ms = magic.open(magic.MAGIC_MIME)
        ms.load()
        check = lambda buff: ms.buffer(buff).startswith("text/")

    for buff in buffers:
        if buff and not check(buff):
            return True
    return False

class AttributeChanger(change.Change):

    """ Make the changes required to a file's attributes """

    def __init__(self, context, filename, user=None, group=None, mode=None):
        self.context = context
        self.filename = filename
        self.user = user
        self.group = group
        self.mode = mode
        self.changed = False

    def apply(self, renderer):
        """ Apply the changes """
        exists = False
        uid = None
        gid = None
        mode = None

        if os.path.exists(self.filename):
            exists = True
            st = os.stat(self.filename)
            uid = st.st_uid
            gid = st.st_gid
            mode = stat.S_IMODE(st.st_mode)

        if self.user is not None:
            try:
                owner = pwd.getpwnam(self.user)
            except KeyError:
                if not self.context.simulate:
                    raise error.InvalidUser("User '%s' not found" % self.user)
                self.context.changelog.info("User '%s' not found; assuming this recipe will create it" % self.user)
                owner = None

            if not owner or owner.pw_uid != uid:
                self.context.shell.execute(["/bin/chown", self.user, self.filename])
                self.changed = True

        if self.group is not None:
            try:
                group = grp.getgrnam(self.group)
            except KeyError:
                if not self.context.simulate:
                    raise error.InvalidGroup("No such group '%s'" % self.group)
                self.context.changelog.info("Group '%s' not found; assuming this recipe will create it" % self.group) #FIXME
                group = None

            if not group or group.gr_gid != gid:
                self.context.shell.execute(["/bin/chgrp", self.group, self.filename])
                self.changed = True

        if self.mode is not None and mode is not None:
            if mode != self.mode:
                self.context.shell.execute(["/bin/chmod", "%o" % self.mode, self.filename])

                # Clear the user and group bits
                # We don't need to set them as chmod will *set* this bits with an octal
                # but won't clear them without a symbolic mode
                if mode & stat.S_ISGID and not self.mode & stat.S_ISGID:
                    self.context.shell.execute(["/bin/chmod", "g-s", self.filename])
                if mode & stat.S_ISUID and not self.mode & stat.S_ISUID:
                    self.context.shell.execute(["/bin/chmod", "u-s", self.filename])

                self.changed = True


class AttributeChangeRenderer(change.TextRenderer):
    renderer_for = AttributeChanger


class FileContentChanger(change.Change):

    """ Apply a content change to a file in a managed way. Simulation mode is
    catered for. Additionally the minimum changes required to the contents are
    applied, and logs of the changes made are recorded. """

    def __init__(self, context, filename, contents, sensitive):
        self.context = context
        self.filename = filename
        self.current = ""
        self.contents = contents
        self.changed = False
        self.renderer = None
        self.sensitive = sensitive

    def empty_file(self):
        """ Write an empty file """
        exists = os.path.exists(self.filename)
        if not exists:
            self.context.shell.execute(["touch", self.filename])
            self.changed = True
        else:
            st = os.stat(self.filename)
            if st.st_size != 0:
                self.renderer.empty_file(self.filename)
                if not self.context.simulate:
                    open(self.filename, "w").close()
                self.changed = True

    def overwrite_existing_file(self):
        """ Change the content of an existing file """
        self.current = open(self.filename).read()
        if self.current != self.contents:
            self.renderer.changed_file(self.filename, self.current, self.contents, self.sensitive)
            if not self.context.simulate:
                open(self.filename, "w").write(self.contents)
            self.changed = True

    def write_new_file(self):
        """ Write contents to a new file. """
        self.renderer.new_file(self.filename, self.contents, self.sensitive)
        if not self.context.simulate:
            open(self.filename, "w").write(self.contents)
        self.changed = True

    def write_file(self):
        """ Write to either an existing or new file """
        exists = os.path.exists(self.filename)
        if exists:
            self.overwrite_existing_file()
        else:
            self.write_new_file()

    def apply(self, renderer):
        """ Apply the changes necessary to the file contents. """
        self.renderer = renderer
        if self.contents is None:
            self.empty_file()
        else:
            self.write_file()


class FileChangeTextRenderer(change.TextRenderer):
    renderer_for = FileContentChanger

    def empty_file(self, filename):
        self.logger.notice("Emptied file %s", filename)

    def new_file(self, filename, contents, sensitive):
        self.logger.notice("Writting new file '%s'" % filename)
        if not sensitive:
            self.diff("", contents)

    def changed_file(self, filename, previous, replacement, sensitive):
        self.logger.notice("Changed file %s", filename)
        if not sensitive:
            self.diff(previous, replacement)

    def diff(self, previous, replacement):
        if not binary_buffers(previous, replacement):
            diff = "".join(difflib.unified_diff(previous.splitlines(1), replacement.splitlines(1)))
            for l in diff.splitlines():
                self.logger.info("    %s", l)
        else:
            self.logger.notice("Binary contents; not showing delta")


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

    def check_path(self, directory, simulate):
        frags = directory.split("/")
        path = "/"
        for i in frags:
            path = os.path.join(path, i)
            if not os.path.exists(path): #FIXME
                if not simulate:
                    raise error.PathComponentMissing(path)
            elif not os.path.isdir(path):
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

    def apply(self, context):
        name = self.resource.name

        self.check_path(os.path.dirname(name), context.simulate)

        if self.resource.template:
            # set a special line ending
            # this strips the \n from the template line meaning no blank line,
            # if a template variable is undefined. See ./yaybu/recipe/interfaces.j2 for an example
            env = Environment(loader=YaybuTemplateLoader(context), line_statement_prefix='%')
            template = env.get_template(self.resource.template)
            contents = template.render(self.get_template_args()) + "\n" # yuk
            sensitive = self.has_protected_strings()
        elif self.resource.static:
            contents = context.get_file(self.resource.static).read()
            sensitive = False
        elif self.resource.encrypted:
            contents = context.get_decrypted_file(self.resource.encrypted).read()
            sensitive = True
        else:
            contents = None
            sensitive = False

        # If a file doesn't exist we create an empty one. This means we can
        # ensure the user, group and permissions are in their final state
        # *BEFORE* we write to them.
        created = False
        if not os.path.exists(self.resource.name):
            if not context.simulate:
                with open(self.resource.name, "w") as fp:
                    fp.write("")
                    fp.close()
            created = True

        ac = AttributeChanger(context,
                              self.resource.name,
                              self.resource.owner,
                              self.resource.group,
                              self.resource.mode)
        context.changelog.apply(ac)

        fc = FileContentChanger(context, self.resource.name, contents, sensitive)
        context.changelog.apply(fc)

        if created or fc.changed or ac.changed:
            return True

class RemoveFile(provider.Provider):
    policies = (resources.file.FileRemovePolicy,)

    @classmethod
    def isvalid(self, *args, **kwargs):
        return super(RemoveFile, self).isvalid(*args, **kwargs)

    def apply(self, context):
        if os.path.exists(self.resource.name):
            if not os.path.isfile(self.resource.name):
                raise error.InvalidProvider("%r: %s exists and is not a file" % (self, self.resource.name))
            context.shell.execute(["/bin/rm", self.resource.name])
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
        return self.resource.hash() != self.resource._original_hash

