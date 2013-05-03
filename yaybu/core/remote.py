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

from yaybu.core.runner import Runner
from yaybu.core.runcontext import RunContext
from yaybu.core import error

import yay

import ssh
import socket
import logging
import time
import subprocess
import pickle
import sys
import os


class TestRemoteRunner(RemoteRunner):

    def serve(self, ctx):
        import shlex
        command = ["/usr/sbin/chroot", self.cwd] + shlex.split(self.get_yaybu_command(ctx))
        p = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, env=self.env, cwd=self.cwd)

        try:
            self.get_server(ctx, p.stdin, p.stdout).serve_forever()

            p.wait()

            if p.returncode == 255:
                raise error.ConnectionError("Could not connect to '%s'" % ctx.host)

            return p.returncode

        finally:
            if p.poll() is None:
                try:
                    p.kill()
                except OSError:
                    if p.poll() is None:
                        raise


