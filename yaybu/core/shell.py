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

    def __init__(self, command, shell, stdin):
        self.command = command
        self.shell = shell
        self.stdin = stdin

    def apply(self, changelog):
        p = subprocess.Popen(self.command,
                             shell=self.shell,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             )
        (self.stdout, self.stderr) = p.communicate(self.stdin)
        self.returncode = p.returncode
        changelog.change(self)

class ShellTextRenderer(change.TextRenderer):

    """ Render a ShellCommand on a textual changelog. """

    renderer_for = ShellCommand

    def render_output(self, name, data, stream):
        if data:
            print >>stream, "shell: ---- %s follows ----" % name
            for l in data.splitlines():
                print >>stream, "shell: ", l
            print >>stream, "shell: ---- %s ends ----" % name

    def render(self, stream):
        print >>stream, "shell: %s" % " ".join(self.original.command)
        print >>stream, "shell: returned %s" % self.original.returncode
        self.render_output("stdout", self.original.stdout, stream)
        self.render_output("stderr", self.original.stderr, stream)

class Shell(object):

    """ This object wraps a shell in yet another shell. When the shell is
    switched into "simulate" mode it can just print what would be done. """

    def __init__(self, context, changelog, simulate=False):
        self.simulate = simulate
        self.context = context
        self.changelog = changelog

    def locate_file(self, filename):
        return self.context.locate_file(filename)

    def execute(self, command, stdin=None, shell=False, passthru=False):
        if self.simulate and not passthru:
            simlog.info(" ".join(command))
            return (0, "", "")
        cmd = ShellCommand(command, shell, stdin)
        cmd.apply(self.changelog)
        return (cmd.returncode, cmd.stdout, cmd.stderr)
