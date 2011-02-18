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

logger = logging.getLogger("shell")
simlog = logging.getLogger("simulation")

class Shell(object):

    """ This object wraps a shell in yet another shell. When the shell is
    switched into "simulate" mode it can just print what would be done. """

    def __init__(self, context, simulate=False):
        self.simulate = simulate
        self.context = context

    def locate_file(self, filename):
        return self.context.locate_file(filename)

    def info(self, msg):
        logger.info(msg)

    def execute(self, command, stdin=None, shell=False, passthru=False):
        if self.simulate and not passthru:
            simlog.info(" ".join(command))
            return (0, "", "")
        logger.info(" ".join(command))
        p = subprocess.Popen(command,
                             shell=shell,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             )
        (stdout, stderr) = p.communicate(stdin)
        if p.returncode != 0:
            logger.info("returned %s" % p.returncode)
        if stderr:
            logger.debug("---- stderr follows ----")
            for l in stderr.split("\n"):
                logger.debug(l)
            logger.debug("---- stderr ends ----")
        return (p.returncode, stdout, stderr)

