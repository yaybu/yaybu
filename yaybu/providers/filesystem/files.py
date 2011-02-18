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

class FileChange(change.Change):

    def __init__(self, filename, old_contents, new_contents):
        self.filename = filename
        self.old_contents = old_contents
        self.new_contents = new_contents

class FileChangeHTMLRenderer(change.HTMLRenderer):
    pass

class FileChangeTextRenderer(change.TextRenderer):
    def render(self):
        print >>self.stream, "Updating file '%s':" % self.resource.name)
        diff = "".join(difflib.context_diff(current.splitlines(1), output.splitlines(1)))
        for l in diff.splitlines():
            print >>self.stream, "    %s" % l

class AttributeChanger:

    """ Make the changes required to a file's attributes """

    def __init__(self, filename, user=None, group=None, mode=None):
        self.filename = filename
        self.user = user
        self.group = group
        self.mode = mode

    def apply(self, shell):
        """ Apply the changes """
        exists = False
        uid = None
        gid = None
        mode = None
        if os.path.exists(self.name):
            exists = True
            st = os.stat(self.name)
            uid = st.st_uid
            gid = st.st_gid
            mode = st.st_mode
            if mode > 32767:
                mode = mode - 32768
        if self.user is not None:
            owner = pwd.getpwnam(self.user)
            if owner.pw_uid != uid:
                shell.execute(["chown", self.user, name])
        if self.group is not None:
            group = grp.getgrnam(self.group)
            if group.gr_gid != gid:
                shell.execute(["chgrp", self.group, name])
        if self.resource.mode is not None:
            if mode != self.mode:
                shell.execute(["chmod", "%o" % self.mode, name])

class FileContentChanger:

    """ Apply a content change to a file in a managed way. Simulation mode is
    catered for. Additionally the minimum changes required to the contents are
    applied, and logs of the changes made are recorded. """

    def __init__(self, filename, contents, backup_filename=None):
        self.filename = filename
        self.backup_filename = backup_filename
        self.contents = contents

    def empty_file(self, shell):
        """ Write an empty file """
        exists = os.path.exists(self.filename)
        if not exists:
            shell.execute(["touch", name])
        else:
            if shell.simulate:
                simlog.info("Emptying contents of file %r" % self.filename)
            else:
                shell.info("# Emptying contents of file %r" % self.filename)
                open(self.filename, "w").close()

    def overwrite_existing_file(self, shell):
        """ Change the content of an existing file """
        current = open(self.filename).read()
        if current != self.contents:
            if shell.simulate:
                # log change
                self.changelog.record(
                    FileChange(self.filename,
                               current,
                               self.contents))
            else:
                open(self.filename).write(output)

    def write_new_file(self, shell):
        """ Write contents to a new file. """
        if shell.simulate:
            simlog.info("Writing new file '%s':" % self.filename)
            for l in output.splitlines():
                simlog.info("    %s" % l)
        else:
            open(self.filename, "w").write(output)

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

class File(provider.Provider):

    """ Provides file creation using templates or static files. """

    policies = (resources.filesystem.FileAppliedPolicy,)

    @classmethod
    def isvalid(self, *args, **kwargs):
        return super(File, self).isvalid(*args, **kwargs)

    def apply(self, shell):
        with shell.changelog.resource(self.resource):
            self._apply(shell)

    def _apply(self, shell):
        name = self.resource.name
        if self.resource.template is None:
            contents = None
        else:
            template = Template(open(self.resource.template).read())
            contents = template.render(**self.resource.template_args)
        fc = FileContentChanger(self.resource.name, contents)
        fc.apply(shell)
        ac = AttributeChanger(self.resource.name,
                              self.resource.owner,
                              self.resource.group,
                              self.resource.mode)
        ac.apply(shell)


