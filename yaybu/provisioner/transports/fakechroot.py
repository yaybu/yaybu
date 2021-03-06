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

from __future__ import absolute_import

import os
import urlparse

from fakechroot import FakeChroot

from . import local, remote, base


class FakechrootTransport(base.Transport, remote.RemoteTransport, local.LocalExecute):

    env_passthrough = [
        "COWDANCER_ILISTFILE",
        "FAKECHROOT",
        "FAKECHROOT_VERSION",
        "FAKECHROOT_BASE",
        "FAKED_MODE",
        "FAKEROOTKEY",
        "LD_PRELOAD",
        "LD_LIBRARY_PATH",
    ]

    def __init__(self, context, *args, **kwargs):
        super(FakechrootTransport, self).__init__(context, *args, **kwargs)

        chroot = FakeChroot(urlparse.urlparse(context.host).path)
        self.env = chroot.get_env()
        self.chroot_path = chroot.chroot_path
        self.overlay_dir = chroot.overlay_dir

    def whoami(self):
        return "root"

    def connect(self):
        pass

    def _execute_impl(self, command, stdin=None, stdout=None, stderr=None):
        paths = [self.overlay_dir]
        if self.env and "PATH" in self.env:
            paths.extend(os.path.join(self.env["FAKECHROOT_BASE"], p.lstrip("/"))
                         for p in self.env["PATH"].split(":"))
        for p in paths:
            path = os.path.join(p, command[0])
            if os.path.exists(path):
                command[0] = path
                break

        return super(FakechrootTransport, self)._execute_impl(
            command,
            stdin=stdin,
            stdout=stdout,
            stderr=stderr,
        )
