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

simlog = logging.getLogger("simulation")

class ShellCommand(change.Change):

    """ Execute and log a change """

    def __init__(self, command, shell, stdin, cwd=None, env=None, verbose=0):
        self.command = command
        self.shell = shell
        self.stdin = stdin
        self.cwd = cwd
        self.env = env
        self.verbose = verbose

    def apply(self, changelog):
        try:
            p = subprocess.Popen(self.command,
                                 shell=self.shell,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 cwd=self.cwd,
                                 env=self.env,
                                 )
            (self.stdout, self.stderr) = p.communicate(self.stdin)
        except:
            logging.error("Exception when running %r" % self.command)
            raise
        self.returncode = p.returncode
        changelog.change(self)

class ShellTextRenderer(change.TextRenderer):

    """ Render a ShellCommand on a textual changelog. """

    renderer_for = ShellCommand

    def render_output(self, cmd, name, data, logger):
        if data:
            cmd("---- {0} follows ----", name)
            for l in data.splitlines():
                cmd("{0}", l)
            cmd("---- {0} ends ----", name)

    def render(self, logger):
        logger.notice(" ".join(self.original.command))
        if self.original.verbose >= 1 and self.original.returncode != 0:
            logger.notice("returned {0}", self.original.returncode)
        if self.original.verbose >= 2:
            self.render_output(logger.info, "stdout", self.original.stdout, logger)
        if self.original.verbose >= 1:
            self.render_output(logger.info, "stderr", self.original.stderr, logger)


class Shell(object):

    """ This object wraps a shell in yet another shell. When the shell is
    switched into "simulate" mode it can just print what would be done. """

    def __init__(self, context, changelog, verbose=0, simulate=False):
        self.simulate = simulate
        self.context = context
        self.changelog = changelog
        self.verbose = verbose

    def locate_bin(self, filename):
        return self.context.locate_bin(filename)

    def execute(self, command, stdin=None, shell=False, passthru=False, cwd=None, env=None, exceptions=True):
        if self.simulate and not passthru:
            simlog.info(" ".join(command))
            return (0, "", "")
        cmd = ShellCommand(command, shell, stdin, cwd, env, self.verbose)
        cmd.apply(self.changelog)
        if exceptions and cmd.returncode != 0:
            raise error.ExecutionError("Non zero return code from %r" % command)
        return (cmd.returncode, cmd.stdout, cmd.stderr)
