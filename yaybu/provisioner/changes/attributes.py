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

import stat

from yaybu import error, changes
from .execute import ShellCommand


class AttributeChanger(changes.Change):

    """ Make the changes required to a file's attributes """

    def __init__(self, filename, user=None, group=None, mode=None):
        self.filename = filename
        self.user = user
        self.group = group
        self.mode = mode
        self.changed = False

    def apply(self, context, renderer):
        """ Apply the changes """

        transport = context.transport
        exists = False
        uid = None
        gid = None
        mode = None

        if transport.exists(self.filename):
            exists = True
            st = transport.stat(self.filename)
            uid = st.st_uid
            gid = st.st_gid
            mode = stat.S_IMODE(st.st_mode)

        if self.user is not None:
            try:
                owner = transport.getpwnam(self.user)
            except KeyError:
                if not context.simulate:
                    raise error.InvalidUser("User '%s' not found" % self.user)
                context.changelog.info("User '%s' not found; assuming this recipe will create it" % self.user)
                owner = None

            if not owner or owner.pw_uid != uid:
                context.change(ShellCommand(["/bin/chown", self.user, self.filename]))
                self.changed = True

        if self.group is not None:
            try:
                group = transport.getgrnam(self.group)
            except KeyError:
                if not context.simulate:
                    raise error.InvalidGroup("No such group '%s'" % self.group)
                context.changelog.info("Group '%s' not found; assuming this recipe will create it" % self.group) #FIXME
                group = None

            if not group or group.gr_gid != gid:
                context.change(ShellCommand(["/bin/chgrp", self.group, self.filename]))
                self.changed = True

        if self.mode is not None and mode is not None:
            if mode != self.mode:
                context.change(ShellCommand(["/bin/chmod", "%o" % self.mode, self.filename]))

                # Clear the user and group bits
                # We don't need to set them as chmod will *set* this bits with an octal
                # but won't clear them without a symbolic mode
                if mode & stat.S_ISGID and not self.mode & stat.S_ISGID:
                    context.change(ShellCommand(["/bin/chmod", "g-s", self.filename]))
                if mode & stat.S_ISUID and not self.mode & stat.S_ISUID:
                    context.change(ShellCommand(["/bin/chmod", "u-s", self.filename]))

                self.changed = True

        return self

