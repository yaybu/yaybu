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
import os, getpass, pwd, grp

class ShellCommand(change.Change):

    """ Execute and log a change """

    def __init__(self, command, shell, stdin, cwd=None, env=None, verbose=0, passthru=False, user=None, group=None):
        self.command = command
        self.shell = shell
        self.stdin = stdin
        self.cwd = cwd
        self.env = env
        self.verbose = verbose
        self.passthru = passthru

        self.user = user
        if user:
            self.uid = pwd.getpwnam(user).pw_uid
        else:
            self.uid = None

        self.group = group
        if group:
            self.gid = grp.getgrnam(self.group).gr_gid
        else:
            self.gid = None

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

    def apply(self, renderer):
        command = self.command[:]

        if not self.passthru:
            renderer.command(command)

        try:
            p = subprocess.Popen(command,
                                 shell=self.shell,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 cwd=self.cwd,
                                 env=self.env,
                                 preexec_fn=self.preexec,
                                 )
            (self.stdout, self.stderr) = p.communicate(self.stdin)
            self.returncode = p.returncode
            renderer.output(p.returncode, self.stdout, self.stderr, self.passthru)
        except Exception, e:
            logging.error("Exception when running %r" % command)
            renderer.exception(e)
            raise

class ShellTextRenderer(change.TextRenderer):

    """ Render a ShellCommand on a textual changelog. """

    renderer_for = ShellCommand

    def command(self, command):
        self.logger.notice(" ".join(command))

    def render_output(self, cmd, name, data):
        if data:
            cmd("---- {0} follows ----", name)
            for l in data.splitlines():
                cmd("{0}", l)
            cmd("---- {0} ends ----", name)

    def output(self, returncode, stdout, stderr, passthru):
        if self.verbose >= 1 and returncode != 0 and not passthru:
            self.logger.notice("returned {0}", returncode)
        if self.verbose >= 2 and not passthru:
            self.render_output(self.logger.info, "stdout", stdout)
        if self.verbose >= 1:
            self.render_output(self.logger.info, "stderr", stderr)

    def exception(self, exception):
        self.logger.notice("Exception: %r" % exception)

class Shell(object):

    """ This object wraps a shell in yet another shell. When the shell is
    switched into "simulate" mode it can just print what would be done. """

    def __init__(self, context, verbose=0, simulate=False):
        self.simulate = context.simulate
        self.verbose = context.verbose
        self.context = context

    def locate_bin(self, filename):
        return self.context.locate_bin(filename)

    def execute(self, command, stdin=None, shell=False, passthru=False, cwd=None, env=None, exceptions=True, user=None, group=None):
        if self.simulate and not passthru:
            self.context.changelog.simlog_info(" ".join(command))
            return (0, "", "")
        cmd = ShellCommand(command, shell, stdin, cwd, env, self.verbose, passthru, user, group)
        self.context.changelog.apply(cmd)
        if exceptions and cmd.returncode != 0:
            self.context.changelog.info("{0}", cmd.stdout)
            self.context.changelog.notice("{0}", cmd.stderr)
            raise error.SystemError(cmd.returncode)
        return (cmd.returncode, cmd.stdout, cmd.stderr)
