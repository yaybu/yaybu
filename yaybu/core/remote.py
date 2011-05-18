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

import subprocess
import json

import yay

from yaybu.core.protocol.server import Server, HttpResource, StaticResource
from yaybu.core.protocol.file import FileResource, EncryptedResource
from yaybu.core.protocol.changelog import ChangeLogResource

from yaybu.core.runner import Runner
from yaybu.core.runcontext import RunContext


class RemoteRunner(Runner):

    def run(self, opts, args):
        self.configure_logging(opts)

        rc = RunContext(args[0], opts)

        if ":" in opts.host:
            host, port = opts.host.rsplit(":", 1)
            connect_args = [host, "-p", port]
        else:
            connect_args = [host]

        command = ["ssh", "-A"] + connect_args + ["yaybu", "--remote"]

        if opts.user:
            command.extend(["--user", opts.user])

        if opts.simulate:
            command.append("-s")

        if opts.verbose:
            command.extend(list("-v" for x in range(opts.verbose)))

        command.append("-")

        try:
            p = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE)

            root = HttpResource()
            root.put_child("config", StaticResource(json.dumps(rc.get_config())))
            root.put_child("files", FileResource())
            root.put_child("encrypted", EncryptedResource())
            root.put_child("changelog", ChangeLogResource())

            Server(rc, root, p.stdout, p.stdin).serve_forever()
            sys.exit(p.wait())

        except error.Error, e:
            p.kill()
            sys.exit(e.returncode)

        return 0

