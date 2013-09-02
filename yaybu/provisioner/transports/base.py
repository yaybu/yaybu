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

import os
from subprocess import list2cmdline
from yay.ast import AST


class Transport(object):

    """ This object wraps a shell in yet another shell. When the shell is
    switched into "simulate" mode it can just print what would be done. """

    env = None
    env_passthrough = []

    def __init__(self, context, verbose=0, simulate=False):
        self.simulate = context.simulate
        self.verbose = context.verbose
        self.context = context

    def execute(self, command, user="root", group=None, stdin=None, env=None, shell=False, cwd=None, umask=None, expected=0, stdout=None, stderr=None):
        # No need to change user if we are already the right one
        if not user:
            user = self.whoami()

        changeuser = (user != self.whoami())

        full_command = []
        if changeuser or group:
            full_command.append('sudo')
        if changeuser:
            full_command.extend(['-u', user])
        if group:
            full_command.extend(['-g', group])
        if changeuser or group:
            full_command.append("--")

        if isinstance(command, list):
            command = command[:]
            for i, segment in enumerate(command):
                if isinstance(segment, AST):
                    command[i] = segment.as_string()
            command = list2cmdline(command)

        parts = []

        newenv = {}
        if self.env_passthrough:
            for var in self.env_passthrough:
                if var in os.environ:
                    newenv[var] = os.environ[var]

        if self.env:
            newenv.update(self.env)

        newenv.update({
            #"HOME": "/home/" + self.user,
            "LOGNAME": user,
            "PATH": "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
            "SHELL": "/bin/sh",
            })

        if env:
            newenv.update(env)

        full_command.extend(["env", "-i"])
        for k, v in newenv.items():
            full_command.append("%s=%s" % (k, v))

        parts = []
        if umask:
            parts.append("umask %o" % umask)

        parts.extend([
            "cd %s" % (cwd or "/"),
            command,
            ])

        full_command.extend(["sh", "-c", "; ".join(parts)])
        return self._execute(full_command, stdin, stdout, stderr)

