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

simlog = logging.getLogger("simulation")

class ShellCommand(change.Change):

    """ Execute and log a change """

    def __init__(self, command, shell, stdin, cwd=None, env=None):
        self.command = command
        self.shell = shell
        self.stdin = stdin
        self.cwd = cwd
        self.env = env

    def apply(self, changelog):
        p = subprocess.Popen(self.command,
                             shell=self.shell,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             cwd=self.cwd,
                             env=self.env,
                             )
        (self.stdout, self.stderr) = p.communicate(self.stdin)
        self.returncode = p.returncode
        changelog.change(self)

class ShellTextRenderer(change.TextRenderer):

    """ Render a ShellCommand on a textual changelog. """

    renderer_for = ShellCommand

    def render_output(self, cmd, name, data, logger):
        if data:
            cmd("---- {0} follows ----", name)
            for l in data.splitlines():
                cmd(l)
            cmd("---- {0} ends ----", name)

    def render(self, logger):
        logger.notice(" ".join(self.original.command))
        if self.original.returncode != 0:
            logger.notice("returned {0}", self.original.returncode)
            self.render_output(logger.notice, "stdout", self.original.stdout, logger)
            self.render_output(logger.notice, "stderr", self.original.stderr, logger)
        else:
            self.render_output(logger.info, "stdout", self.original.stdout, logger)
            self.render_output(logger.info, "stderr", self.original.stderr, logger)


class Shell(object):

    """ This object wraps a shell in yet another shell. When the shell is
    switched into "simulate" mode it can just print what would be done. """

    def __init__(self, context, changelog, simulate=False):
        self.simulate = simulate
        self.context = context
        self.changelog = changelog

    def locate_file(self, filename):
        return self.context.locate_file(filename)

    def execute(self, command, stdin=None, shell=False, passthru=False, cwd=None, env=None):
        if self.simulate and not passthru:
            simlog.info(" ".join(command))
            return (0, "", "")
        cmd = ShellCommand(command, shell, stdin, cwd, env)
        cmd.apply(self.changelog)
        return (cmd.returncode, cmd.stdout, cmd.stderr)
