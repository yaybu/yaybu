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

    def communicate(self, p, stdout_fn=lambda x: None, stderr_fn=lambda x: None):
        if p.stdin:
            p.stdin.flush()
            p.stdin.close()

        callbacks = {}
        out = {}

        if p.stdout:
            callbacks[p.stdout] = stdout_fn
            out[p.stdout] = []

        if p.stderr:
            callbacks[p.stderr] = stderr_fn
            out[p.stderr] = []

        while len(callbacks.keys()):
            try:
                rlist, wlist, xlist = select.select(callbacks.keys(), [], [])
            except select.error, e:
                if e.args[0] == errno.EINTR:
                    continue
                raise

            for r in rlist:
                data = os.read(r.fileno(), 1024)
                if data == "":
                    del callbacks[r]
                    r.close()
                else:
                    out[r].append
                    if p.universal_newlines and hasattr(file, 'newlines'):
                        data = p._translate_newlines(data)
                    callbacks[r](data)

        returncode = p.wait()

        if p.stdout:
            stdout = ''.join(out[p.stdout])
            if p.universal_newlines and hasattr(file, 'newlines'):
                stdout = p._translate_newlines(stdout)
        else:
            stdout = ''

        if p.stderr:
            stderr = ''.join(out[p.stderr])
            if p.universal_newlines and hasattr(file, 'newlines'):
                stderr = p._translate_newlines(stderr)
        else:
            stderr = ''

        return returncode, stdout, stderr

    def apply(self, renderer):
        command = self.command[:]

        renderer.passthru = self.passthru

        # Inherit parent environment
        if not self.env:
            env = None
        else:
            env = os.environ.copy()
            env.update(self.env)

        try:
            p = subprocess.Popen(command,
                                 shell=self.shell,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 cwd=self.cwd,
                                 env=env,
                                 preexec_fn=self.preexec,
                                 )
            self.returncode, self.stdout, self.stderr = self.communicate(p, renderer.stdout, renderer.stderr)
            renderer.output(p.returncode)
        except Exception, e:
            logging.error("Exception when running %r" % command)
            renderer.exception(e)
            raise

class ShellTextRenderer(change.TextRenderer):

    """ Render a ShellCommand on a textual changelog. """

    renderer_for = ShellCommand
    passthru = False

    def command(self, command):
        if not self.passthru:
            self.logger.notice("$ " + " ".join(command))

    def output(self, returncode):
        if self.verbose >= 1 and returncode != 0 and not self.passthru:
            self.logger.notice("returned {0}", returncode)

    def stdout(self, data):
       if self.verbose >= 2 and not self.passthru:
           for l in data.splitlines():
               self.logger.info(l)

    def stderr(self, data):
        if self.verbose >= 1:
            for l in data.splitlines():
                self.logger.info(l)

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

