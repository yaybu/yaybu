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

from jinja2 import Environment

from yaybu import resources
from yaybu.core import provider
from yaybu.core import change
from yaybu.core import error

def binary_buffers(*buffers):

    """ Check all of the passed buffers to see if any of them are binary. If
    any of them are binary this will return True. """
    if not magic:
        check = lambda buff: any((c in string.printable) for c in buff)
    else:
        ms = magic.open(magic.MAGIC_NONE)
        ms.load()
        check = lambda buff: ms.buffer(buff).endswith("text")

    for buff in buffers:
        if not check(buff):
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
            owner = pwd.getpwnam(self.user)
            if owner.pw_uid != uid:
                self.context.shell.execute(["chown", self.user, self.filename])
                self.changed = True
        if self.group is not None:
            group = grp.getgrnam(self.group)
            if group.gr_gid != gid:
                self.context.shell.execute(["chgrp", self.group, self.filename])
                self.changed = True
        if self.mode is not None:
            if mode != self.mode:
                self.context.shell.execute(["chmod", "%o" % self.mode, self.filename])

                # Clear the user and group bits
                # We don't need to set them as chmod will *set* this bits with an octal
                # but won't clear them without a symbolic mode
                if mode & stat.S_ISGID and not self.mode & stat.S_ISGID:
                    self.context.shell.execute(["chmod", "g-s", self.filename])
                if mode & stat.S_ISUID and not self.mode & stat.S_ISUID:
                    self.context.shell.execute(["chmod", "u-s", self.filename])

                self.changed = True

class FileContentChanger(change.Change):

    """ Apply a content change to a file in a managed way. Simulation mode is
    catered for. Additionally the minimum changes required to the contents are
    applied, and logs of the changes made are recorded. """

    def __init__(self, context, filename, contents):
        self.context = context
        self.filename = filename
        self.current = ""
        self.contents = contents
        self.changed = False
        self.renderer = None

    def empty_file(self):
        """ Write an empty file """
        exists = os.path.exists(self.filename)
        if not exists:
            self.context.shell.execute(["touch", self.filename])
            self.changed = True
        else:
            st = os.stat(self.filename)
            if st.st_size != 0:
                if self.context.simulate:
                    self.renderer.simulation_info("Emptying contents of file {0!r}" % self.filename)
                else:
                    self.renderer.empty_file(self.filename)
                    open(self.filename, "w").close()
                self.changed = True

    def overwrite_existing_file(self):
        """ Change the content of an existing file """
        self.current = open(self.filename).read()
        if self.current != self.contents:
            if self.context.simulate:
                self.renderer.simulation_info("Overwriting new file '%s':" % self.filename)
                if not binary_buffers(self.contents):
                    for l in self.contents.splitlines():
                        self.renderer.simulation_info("    %s" % l)
            else:
                open(self.filename, "w").write(self.contents)
            self.changed = True

    def write_new_file(self):
        """ Write contents to a new file. """
        if self.context.simulate:
            self.renderer.simulation_info("Writing new file '%s':" % self.filename)
            if not binary_buffers(self.contents):
                for l in self.contents.splitlines():
                    self.renderer.simulation_info("    %s" % l)
        else:
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
        self.logger.notice("Emptied file {0!r}", filename)

    def changed_file(self, filename, previous, replacement):
        self.logger.notice("Changed file {0!r}", filename)
        if replacement is not None:
            if not binary_buffers(previous, replacement):
                diff = "".join(difflib.context_diff(previous.splitlines(1), replacement.splitlines(1)))
                for l in diff.splitlines():
                    self.logger.info("    {0}", l)

class File(provider.Provider):

    """ Provides file creation using templates or static files. """

    policies = (resources.file.FileApplyPolicy,)

    @classmethod
    def isvalid(self, *args, **kwargs):
        return super(File, self).isvalid(*args, **kwargs)

    def check_path(self, directory):
        frags = directory.split("/")
        path = "/"
        for i in frags:
            path = os.path.join(path, i)
            if not os.path.exists(path):
                raise error.PathComponentMissing(path)
            if not os.path.isdir(path):
                raise error.PathComponentNotDirectory(path)

    def apply(self, context):
        name = self.resource.name

        self.check_path(os.path.dirname(name))

        if self.resource.template:
            # set a special line ending
            # this strips the \n from the template line meaning no blank line,
            # if a template variable is undefined. See ./yaybu/recipe/interfaces.j2 for an example
            env = Environment(line_statement_prefix='%')
            template = env.from_string(context.get_file(self.resource.template).read())
            contents = template.render(self.resource.template_args) + "\n" # yuk
        elif self.resource.static:
            contents = context.get_file(self.resource.static).read()
        elif self.resource.encrypted:
            contents = context.get_decrypted_file(self.resource.encrypted).read()
        else:
            contents = None

        fc = FileContentChanger(context, self.resource.name, contents)
        context.changelog.apply(fc)
        ac = AttributeChanger(context,
                              self.resource.name,
                              self.resource.owner,
                              self.resource.group,
                              self.resource.mode)
        context.changelog.apply(ac)
        if fc.changed or ac.changed:
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
            context.shell.execute(["rm", self.resource.name])
            changed = True
        else:
            context.changelog.info("File %s missing already so not removed" % self.resource.name)
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

