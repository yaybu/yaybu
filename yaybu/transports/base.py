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

from ..core import change, error

class Command(String):
    """ Horrible horrible cludge """
    pass


class ShellCommand(change.Change):

    """ Execute and log a change """

    def __init__(self, factory, command, shell, stdin, cwd=None, env=None, env_passthru=None, verbose=0, inert=False, user=None, group=None, simulate=False, umask=None):
        self.factory = factory
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

        self.user = None
        self.group = None
        self.homedir = None

        self.umask = umask

    def _tounicode(self, l):
        """ Ensure all elements of the list are unicode """
        def uni(x):
            if type(x) is type(u""):
                return x
            return unicode(x, "utf-8")
        return map(uni, l)

    def apply(self, renderer):
        ctx = self.factory.context
        vfs = ctx.vfs

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
            if not vfs.exists(os.path.join(self.cwd, command[0][2:])):
                command_exists = False

        elif command[0].startswith("/"):
            if not vfs.exists(command[0]):
                command_exists = False

        else:
            for path in env["PATH"].split(":"):
                if vfs.exists(os.path.join(path, command[0])):
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

        self.returncode, self.stdout, self.stderr = self.factory._execute(command, renderer, stdin=self.stdin, env=env)


class ShellTextRenderer(change.TextRenderer):

    """ Render a ShellCommand on a textual changelog. """

    renderer_for = ShellCommand
    inert = False

    def command(self, command):
        if not self.inert:
            self.logger.notice(u"# " + u" ".join(command))

    def output(self, returncode):
        if self.verbose >= 1 and returncode != 0 and not self.inert:
            self.logger.notice("returned %s", returncode)

    def stdout(self, data):
        if self.verbose >= 2 and not self.inert:
            self.logger.info(data)

    def stderr(self, data):
        if self.verbose >= 1:
            self.logger.info(data)

    def exception(self, exception):
        self.logger.notice("Exception: %r" % exception)


class Shell(object):

    """ This object wraps a shell in yet another shell. When the shell is
    switched into "simulate" mode it can just print what would be done. """

    def __init__(self, context, verbose=0, simulate=False, environment=None):
        self.simulate = context.simulate
        self.verbose = context.verbose
        self.context = context

        self.environment = ["SSH_AUTH_SOCK"]
        if environment:
            self.environment.extend(environment)

    def execute(self, command, stdin=None, shell=False, inert=False, cwd=None, env=None, user=None, group=None, umask=None, expected=0):
        cmd = ShellCommand(self, command, shell, stdin, cwd, env, self.environment, self.verbose, inert, user, group, self.simulate, umask)
        self.context.changelog.apply(cmd)
        if expected is not None and cmd.returncode != 0:
            raise error.SystemError(cmd.returncode, cmd.stdout, cmd.stderr)
        return (cmd.returncode, cmd.stdout, cmd.stderr)

