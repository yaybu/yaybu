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
import pickle
import sys
import os

import yay

from yaybu.core.protocol.server import Server, HttpResource, StaticResource
from yaybu.core.protocol.file import FileResource, EncryptedResource
from yaybu.core.protocol.changelog import ChangeLogResource

from yaybu.core.runner import Runner
from yaybu.core.runcontext import RunContext
from yaybu.core import error


class RemoteRunner(Runner):

    user_known_hosts_file = "/dev/null"
    strict_host_key_checking = "ask"

    def load_host_keys(self, filename):
        self.user_known_hosts_file = filename

    def load_system_host_keys(self):
        self.user_known_hosts_file = os.path.expanduser("~/.ssh/known_hosts")

    def set_missing_host_key_policy(self, policy):
        self.strict_host_key_checking = policy

    def run(self, ctx):
        command = ["ssh", "-A"]
        command.extend(["-o", "UserKnownHostsFile %s" % self.user_known_hosts_file])
        command.extend(["-o", "StrictHostKeyChecking %s" % self.strict_host_key_checking])

        if ":" in ctx.host:
            host, port = ctx.host.rsplit(":", 1)
            command.extend([host, "-p", port])
        else:
            command.append(ctx.host)

        command.extend(["yaybu", "--remote"])

        if ctx.user:
            command.extend(["--user", ctx.user])

        if ctx.simulate:
            command.append("-s")

        if ctx.verbose:
            command.extend(list("-v" for x in range(ctx.verbose)))

        if ctx.resume:
            command.append("--resume")

        if ctx.no_resume:
            command.append("--no-resume")

        command.append("-")

        try:
            p = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE)

            root = HttpResource()
            root.put_child("config", StaticResource(pickle.dumps(ctx.get_config())))
            root.put_child("files", FileResource())
            root.put_child("encrypted", EncryptedResource())
            root.put_child("changelog", ChangeLogResource())

            Server(ctx, root, p.stdout, p.stdin).serve_forever()
            p.wait()
            return p.returncode

        except error.Error, e:
            print >>sys.stderr, "Error: %s" % str(e)

            p.kill()
            return e.returncode

        return p.returncode

