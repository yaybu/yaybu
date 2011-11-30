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

import logging
import subprocess
import StringIO
import change
import error
import os, getpass, pwd, grp, select
import shlex

from yay import String

class Command(String):
    """ Horrible horrible cludge """
    pass


class Handle(object):

    def __init__(self, handle, callback=None):
        self.handle = handle
        self.callback = callback
        self._output = []

    def fileno(self):
        return self.handle.fileno()

    def read(self):
        data = os.read(self.fileno(), 1024)
        if data == "":
            self.handle.close()
            return False

        self._output.append(data)

        if self.callback:
            for l in data.splitlines():
                self.callback(l + "\r")

        return True

    def isready(self):
        return bool(self.handle)

    @property
    def output(self):
        out = ''.join(self._output)
        return out


class ShellCommand(change.Change):

    """ Execute and log a change """

    def __init__(self, command, shell, stdin, cwd=None, env=None, env_passthru=None, verbose=0, passthru=False, user=None, group=None, simulate=False, logas=None):
        self.command = command
        self.shell = shell
        self.stdin = stdin
        self.cwd = cwd
        self.env = env
        self.env_passthru = env_passthru
        self.verbose = verbose
        self.passthru = passthru
        self.simulate = simulate
        self.logas = logas
        self._generated_env = {}

        self.user = None
        self.uid = None
        self.group = None
        self.gid = None
        self.homedir = None

        if self.simulate and not self.passthru:
            # For now, we skip this setup in simulate mode - not sure it will ever be possible
            return

        self.user = user
        if user:
            u = pwd.getpwnam(user)
            self.uid = u.pw_uid
            self.homedir = u.pw_dir
        else:
            self.uid = None
            self.homedir = pwd.getpwuid(os.getuid()).pw_dir
            self.user = pwd.getpwuid(os.getuid()).pw_name

        self.group = group
        if group:
            self.gid = grp.getgrnam(self.group).gr_gid

    def preexec(self):
        if self.uid is not None:
            if self.uid != os.getuid():
                os.setuid(self.uid)
            if self.uid != os.geteuid():
                os.seteuid(self.uid)

        if self.gid is not None:
            if self.gid != os.getgid():
                os.setgid(self.gid)
            if self.gid != os.getegid():
                os.setegid(self.gid)

        os.environ.clear()
        os.environ.update(self._generated_env)

    def communicate(self, p, stdout_fn=None, stderr_fn=None):
        if p.stdin:
            p.stdin.flush()
            p.stdin.close()

        stdout = Handle(p.stdout, stdout_fn)
        stderr = Handle(p.stderr, stderr_fn)

        # Initial readlist is any handle that is valid
        readlist = [h for h in (stdout, stderr) if h.isready()]

        while readlist:
            try:
                rlist, wlist, xlist = select.select(readlist, [], [])
            except select.error, e:
                if e.args[0] == errno.EINTR:
                    continue
                raise

            # Read from all handles that select told us can be read from
            # If they return false then we are at the end of the stream
            # and stop reading from them
            for r in rlist:
                if not r.read():
                    readlist.remove(r)

        returncode = p.wait()

        return returncode, stdout.output, stderr.output

    def _tounicode(self, l):
        """ Ensure all elements of the list are unicode """
        def uni(x):
            if type(x) is type(u""):
                return x
            return unicode(x, "utf-8")
        return map(uni, l)

    def apply(self, renderer):
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

        renderer.passthru = self.passthru
        renderer.command(self.logas or logas)

        env = {
            "HOME": self.homedir,
            "LOGNAME": self.user,
            "PATH": "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
            "SHELL": "/bin/sh",
            }

        if self.env_passthru:
            for var in self.env_passthru:
                if var in os.environ:
                    env[var] = os.environ[var]

        if self.env:
            env.update(self.env)

        self._generated_env = env

        if self.simulate and not self.passthru:
            self.returncode = 0
            self.stdout = ""
            self.stderr = ""
            return

        try:
            p = subprocess.Popen(command,
                                 shell=self.shell,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 cwd=self.cwd,
                                 env=None,
                                 preexec_fn=self.preexec,
                                 )
            self.returncode, self.stdout, self.stderr = self.communicate(p, renderer.stdout, renderer.stderr)
            renderer.output(p.returncode)
        except Exception, e:
            renderer.exception(e)
            raise

class ShellTextRenderer(change.TextRenderer):

    """ Render a ShellCommand on a textual changelog. """

    renderer_for = ShellCommand
    passthru = False

    def command(self, command):
        if not self.passthru:
            self.logger.notice(u"# " + u" ".join(command))

    def output(self, returncode):
        if self.verbose >= 1 and returncode != 0 and not self.passthru:
            self.logger.notice("returned %s", returncode)

    def stdout(self, data):
       if self.verbose >= 2 and not self.passthru:
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

    def locate_bin(self, filename):
        return self.context.locate_bin(filename)

    def execute(self, command, stdin=None, shell=False, passthru=False, cwd=None, env=None, exceptions=True, user=None, group=None, logas=None):
        cmd = ShellCommand(command, shell, stdin, cwd, env, self.environment, self.verbose, passthru, user, group, self.simulate, logas)
        self.context.changelog.apply(cmd)
        if exceptions and cmd.returncode != 0:
            self.context.changelog.info(cmd.stdout)
            self.context.changelog.notice(cmd.stderr)
            raise error.SystemError(cmd.returncode)
        return (cmd.returncode, cmd.stdout, cmd.stderr)

