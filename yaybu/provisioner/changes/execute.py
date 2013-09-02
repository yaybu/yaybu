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

import posixpath
import shlex

from yay import String
from yay.ast import AST

from yaybu import error, changes


class Command(String):
    """ Horrible horrible cludge """
    pass


class ShellCommand(changes.Change):

    """ Execute and log a change """

    changed = True

    def __init__(self, command, shell=None, stdin=None, cwd=None, env=None, user="root", group=None, umask=None, expected=0):
        self.command = command
        self.shell = shell
        self.stdin = stdin
        self.cwd = cwd
        self.env = env

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
            raise NotImplementedError
        elif isinstance(self.command, String):
            raise NotImplementedError
        elif isinstance(self.command, list):
            command = []
            for c in self.command:
                if isinstance(c, AST):
                    command.append(c.as_string())
                else:
                    command.append(c)
            logas = []
            for c in self.command:
                if isinstance(c, AST):
                    logas.append(c.as_safe_string())
                else:
                    logas.append(c)
        elif isinstance(self.command, basestring):
            logas = command = shlex.split(self.command.encode("UTF-8"))
        elif isinstance(self.command, AST):
            command = shlex.split(self.command.as_string().encode("UTF-8"))
            logas = shlex.split(self.command.as_safe_string().encode("UTF-8"))

        command = self._tounicode(command)
        logas = self._tounicode(logas)
        renderer.command(logas)

        env = {
            "PATH": "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
            }

        if self.env:
            for key, item in self.env.iteritems():
                if isinstance(item, String):
                    env[key] = item.unprotected.encode("UTF-8")
                else:
                    env[key] = item

        if ctx.simulate:
            self.returncode = 0
            self.stdout = ""
            self.stderr = ""
            return

        command_exists = True
        if command[0].startswith("./"):
            if len(command[0]) <= 2:
                command_exists = False
            if not transport.exists(posixpath.join(self.cwd, command[0][2:])):
                command_exists = False

        elif command[0].startswith("/"):
            if not transport.exists(command[0]):
                command_exists = False

        else:
            for path in env["PATH"].split(":"):
                if transport.exists(posixpath.join(path, command[0])):
                    break
            else:
                command_exists = False

        if not command_exists:
            if not ctx.simulate:
                raise error.BinaryMissing("Command '%s' not found" % command[0])
            renderer.stderr("Command '%s' not found; assuming this recipe will create it" % command[0])
            self.returncode = 0
            self.stdout = ""
            self.stderr = ""
            return

        self.returncode, self.stdout, self.stderr = transport.execute(command, stdin=self.stdin, stdout=renderer.stdout, stderr=renderer.stderr, env=env, user=self.user, group=self.group, cwd=self.cwd, umask=self.umask)
        renderer.flush()

        if self.expected is not None and self.returncode != self.expected:
            raise error.SystemError(self.returncode, self.stdout, self.stderr)


def _handle_slash_r(line):
    line = line.rstrip("\r")
    if "\r" in line:
        line = line.rsplit("\r", 1)[1]
    return line


class ShellTextRenderer(changes.TextRenderer):

    """ Render a ShellCommand on a textual changelog. """

    renderer_for = ShellCommand

    stdout_buffer = ""
    stderr_buffer = ""

    def command(self, command):
        self.logger.notice(u"# " + u" ".join(command))

    def output(self, returncode):
        if self.verbose >= 1 and returncode != 0 and not self.inert:
            self.logger.notice("returned %s", returncode)

    def stdout(self, data):
        if self.verbose >= 2:
            data = self.stdout_buffer + data
            if not "\n" in data:
                self.stdout_buffer = data
                return
            data, self.stdout_buffer = data.rsplit("\n", 1)
            for line in data.split("\n"):
                self.logger.info(_handle_slash_r(line))

    def stderr(self, data):
        if self.verbose >= 1:
            data = self.stderr_buffer + data
            if not "\n" in data:
                self.stdout_buffer = data
                return
            data, self.stderr_buffer = data.rsplit("\n", 1)
            for line in data.split("\n"):
                self.logger.info(_handle_slash_r(line))

    def flush(self):
        if self.stdout_buffer:
            self.logger.info(_handle_slash_r(self.stdout_buffer))
        if self.stderr_buffer:
            self.logger.info(_handle_slash_r(self.stderr_buffer))

    def exception(self, exception):
        self.logger.notice("Exception: %r" % exception)
