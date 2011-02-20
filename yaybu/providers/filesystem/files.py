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
import stat
import pwd
import grp
import difflib
import logging

from jinja2 import Template

from yaybu import resources
from yaybu.core import provider
from yaybu.core import change

simlog = logging.getLogger("simulation")

class AttributeChanger(change.Change):

    """ Make the changes required to a file's attributes """

    def __init__(self, filename, user=None, group=None, mode=None):
        self.filename = filename
        self.user = user
        self.group = group
        self.mode = mode
        self.changed = False

    def apply(self, shell):
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
                shell.execute(["chown", self.user, self.filename])
                self.changed = True
        if self.group is not None:
            group = grp.getgrnam(self.group)
            if group.gr_gid != gid:
                shell.execute(["chgrp", self.group, self.filename])
                self.changed = True
        if self.mode is not None:
            if mode != self.mode:
                shell.execute(["chmod", "%o" % self.mode, self.filename])
                self.changed = True

class FileContentChanger(change.Change):

    """ Apply a content change to a file in a managed way. Simulation mode is
    catered for. Additionally the minimum changes required to the contents are
    applied, and logs of the changes made are recorded. """

    def __init__(self, filename, contents, backup_filename=None):
        self.filename = filename
        self.backup_filename = backup_filename
        self.current = ""
        self.contents = contents
        self.changed = False

    def empty_file(self, shell):
        """ Write an empty file """
        exists = os.path.exists(self.filename)
        if not exists:
            shell.execute(["touch", self.filename])
            self.changed = True
        else:
            st = os.stat(self.filename)
            if st.st_size != 0:
                if shell.simulate:
                    simlog.info("Emptying contents of file {0!r}" % self.filename)
                else:
                    shell.changelog.info("# Emptying contents of file {0!r}", self.filename)
                    open(self.filename, "w").close()
                self.changed = True

    def overwrite_existing_file(self, shell):
        """ Change the content of an existing file """
        self.current = open(self.filename).read()
        if self.current != self.contents:
            if shell.simulate:
                # log change
                self.changelog.record(
                    FileChange(self.filename,
                               current,
                               self.contents))
            else:
                open(self.filename).write(output)
            self.changed = True

    def write_new_file(self, shell):
        """ Write contents to a new file. """
        if shell.simulate:
            simlog.info("Writing new file '%s':" % self.filename)
            for l in output.splitlines():
                simlog.info("    %s" % l)
        else:
            open(self.filename, "w").write(self.contents)
        self.changed = True

    def write_file(self, shell):
        """ Write to either an existing or new file """
        exists = os.path.exists(self.filename)
        if exists:
            self.overwrite_existing_file(shell)
        else:
            self.write_new_file(shell)

    def apply(self, shell):
        """ Apply the changes necessary to the file contents. """
        if self.backup_filename is not None:
            raise NotImplementedError
        if self.contents is None:
            self.empty_file(shell)
        else:
            self.write_file(shell)
        shell.changelog.change(self)

class FileChangeTextRenderer(change.TextRenderer):
    renderer_for = FileContentChanger

    def render(self, changelog):
        changelog.notice("Changed file {0!r}", self.original.filename)
        if self.original.contents is not None:
            diff = "".join(difflib.context_diff(self.original.current.splitlines(1), self.original.contents.splitlines(1)))
            for l in diff.splitlines():
                changelog.info("    %s" % l)

class File(provider.Provider):

    """ Provides file creation using templates or static files. """

    policies = (resources.filesystem.FileAppliedPolicy,)

    @classmethod
    def isvalid(self, *args, **kwargs):
        return super(File, self).isvalid(*args, **kwargs)

    def apply(self, shell):
        name = self.resource.name

        if self.resource.template:
            template = Template(open(self.resource.template).read())
            contents = template.render(**self.resource.template_args)
        elif self.resource.static:
            contents = open(self.resource.static).read()
        else:
            contents = ""

        fc = FileContentChanger(self.resource.name, contents)
        fc.apply(shell)
        ac = AttributeChanger(self.resource.name,
                              self.resource.owner,
                              self.resource.group,
                              self.resource.mode)
        ac.apply(shell)
        if fc.changed or ac.changed:
            return True


