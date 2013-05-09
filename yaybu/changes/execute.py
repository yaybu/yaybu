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

import logging
import os
import shlex

from yay import String

from yaybu import error
from .import base

class Command(String):
    """ Horrible horrible cludge """
    pass


class ShellCommand(base.Change):

    """ Execute and log a change """

    def __init__(self, command, shell=None, stdin=None, cwd=None, env=None, env_passthru=None, verbose=0, inert=False, user=None, group=None, simulate=False, umask=None, expected=0):
        self.command = command
        self.shell = shell
        self.stdin = stdin
        self.cwd = cwd
        self.env = env
        self.env_passthru = env_passthru
        self.verbose = verbose
        self.inert = inert
        self.simulate = simulate
        self._generated_env = {}

        self.user = user
        self.group = group
        self.umask = umask
        self.expected = expected

    def _tounicode(self, l):
        """ Ensure all elements of the list are unicode """
        def uni(x):
            if type(x) is type(u""):
                return x
            return unicode(x, "utf-8")
        return map(uni, l)

    def apply(self, ctx, renderer):
        transport = ctx.transport

        if isinstance(self.command, Command):
            logas = self.command.as_list(secret=True)
            command = self.command.as_list(secret=False)
        elif isinstance(self.command, String):
            logas = shlex.split(self.command.protected.encode("UTF-8"))
            command = shlex.split(self.command.unprotected.encode("UTF-8"))
        elif isinstance(self.command, list):
            logas = command = self.command[:]
        elif isinstance(self.command, basestring):
            logas = command = shlex.split(self.command.encode("UTF-8"))

        command = self._tounicode(command)
        logas = self._tounicode(logas)

        renderer.inert = self.inert
        renderer.command(logas)

        env = {
            #"HOME": "/home/" + self.user,
            #"LOGNAME": self.user,
            "PATH": "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
            "SHELL": "/bin/sh",
            }

        if self.env_passthru:
            for var in self.env_passthru:
                if var in os.environ:
                    env[var] = os.environ[var]

        if self.env:
            for key, item in self.env.iteritems():
                if isinstance(item, String):
                    env[key] = item.unprotected.encode("UTF-8")
                else:
                    env[key] = item

        self._generated_env = env

        if self.simulate and not self.inert:
            self.returncode = 0
            self.stdout = ""
            self.stderr = ""
            return

        command_exists = True
        if command[0].startswith("./"):
            if len(command[0]) <= 2:
                command_exists = False
            if not transport.exists(os.path.join(self.cwd, command[0][2:])):
                command_exists = False

        elif command[0].startswith("/"):
            if not transport.exists(command[0]):
                command_exists = False

        else:
            for path in env["PATH"].split(":"):
                if transport.exists(os.path.join(path, command[0])):
                    break
            else:
                command_exists = False

        if not command_exists:
            if not self.simulate:
                raise error.BinaryMissing("Command '%s' not found" % command[0])
            renderer.stderr("Command '%s' not found; assuming this recipe will create it" % command[0])
            self.returncode = 0
            self.stdout = ""
            self.stderr = ""
            return

        self.returncode, self.stdout, self.stderr = transport.execute(command, stdin=self.stdin, stdout=renderer.stdout, stderr=renderer.stderr, env=env, user=self.user, group=self.group, cwd=self.cwd)

        if self.expected is not None and self.returncode != self.expected:
            raise error.SystemError(self.returncode, self.stdout, self.stderr)


class ShellTextRenderer(base.TextRenderer):

    """ Render a ShellCommand on a textual changelog. """

    renderer_for = ShellCommand

    def command(self, command):
        if not self.inert:
            self.logger.notice(u"# " + u" ".join(command))

    def output(self, returncode):
        if self.verbose >= 1 and returncode != 0 and not self.inert:
            self.logger.notice("returned %s", returncode)

    def stdout(self, data):
        if self.verbose >= 2:
            self.logger.info(data)

    def stderr(self, data):
        if self.verbose >= 1:
            self.logger.info(data)

    def exception(self, exception):
        self.logger.notice("Exception: %r" % exception)
