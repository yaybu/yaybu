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

from . import local, remote, base
import os

class FakechrootTransport(base.Transport, remote.RemoteTransport, local.LocalExecute):

    env_passthrought = [
        "COWDANCER_ILISTFILE",
        "FAKECHROOT",
        "FAKECHROOT_VERSION",
        "FAKECHROOT_BASE",
        "FAKED_MODE",
        "FAKEROOTKEY",
        "LD_PRELOAD",
        "LD_LIBRARY_PATH",
        ]

    def whoami(self):
        return "root"

    def connect(self):
        pass

    def _execute(self, command, stdin=None, stdout=None, stderr=None):
        paths = [self.overlay_dir]
        if self.env and "PATH" in self.env:
            paths.extend(os.path.join(self.env["FAKECHROOT_BASE"], p.lstrip("/")) for p in self.env["PATH"].split(":"))
        for p in paths:
            path = os.path.join(p, command[0])
            if os.path.exists(path):
                command[0] = path
                break

        return super(FakechrootTransport, self)._execute(
            command,
            stdin = stdin,
            stdout = stdout,
            stderr = stderr,
            )
