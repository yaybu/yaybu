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

import optparse
import os
import sys
import logging
import logging.handlers
import collections

import yay

from yaybu.core.shell import Shell
from yaybu.core import change
from yaybu.core import resource

logger = logging.getLogger("runner")

class LoaderError(Exception):
    pass

class RunContext:

    simulate = False
    ypath = ()
    verbose = 0
    html = None

    def __init__(self, opts=None):
        self.path = []
        self.ypath = []
        if opts is not None:
            logger.debug("Invoked with ypath: %r" % opts.ypath)
            logger.debug("Environment YAYBUPATH: %r" % os.environ.get("YAYBUPATH", ""))
            self.simulate = opts.simulate
            self.ypath = opts.ypath
            self.verbose = opts.verbose
            if opts.html is not None:
                self.html = open(opts.html, "w")
        if "PATH" in os.environ:
            for term in os.environ["PATH"].split(":"):
                self.path.append(term)
        if "YAYBUPATH" in os.environ:
            for term in os.environ["YAYBUPATH"].split(":"):
                self.ypath.append(term)

    def locate(self, paths, filename):
        if filename.startswith("/"):
            return filename
        for prefix in paths:
            candidate = os.path.realpath(os.path.join(prefix, filename))
            logger.debug("Testing for existence of %r" % (candidate,))
            if os.path.exists(candidate):
                return candidate
            logger.debug("%r does not exist" % candidate)
        raise ValueError("Cannot locate file %r" % filename)

    def locate_file(self, filename):
        """ Locates a file by referring to the defined yaybu path. If the
        filename starts with a / then it is absolutely rooted in the
        filesystem and will be returned unmolested. """
        return self.locate(self.ypath, filename)

    def locate_bin(self, filename):
        """ Locates a binary by referring to the defined yaybu path and PATH. If the
        filename starts with a / then it is absolutely rooted in the
        filesystem and will be returned unmolested. """
        return self.locate(self.ypath + self.path, filename)


class Runner(object):

    resources = None

    def configure_logging(self, opts):
        """ configure the audit trail to log to file or to syslog """
        levels = {
            'debug': logging.DEBUG,
            'info': logging.INFO,
            'warning': logging.WARNING,
            'error': logging.ERROR,
            'critical': logging.CRITICAL,
            }

        log_level = levels.get(opts.log_level, None)
        if log_level is None:
            raise KeyError("Log level %s not recognised, terminating" % opts.log_level)
        if opts.logfile is not None:
            raise NotImplementedError
            if opts.logfile == "-":
                logging.basicConfig(stream=sys.stdout,
                                    format="%(asctime)s %(levelname)s %(message)s",
                                    level=log_level)
            else:
                logging.basicConfig(filename=opts.logfile,
                                    filemode="a",
                                    format="%(asctime)s %(levelname)s %(message)s",
                                    level=log_level)
        else:
            facility = getattr(logging.handlers.SysLogHandler, "LOG_LOCAL%s" % opts.log_facility)
            handler = logging.handlers.SysLogHandler("/dev/log", facility=facility)
            formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
            handler.setFormatter(formatter)
            logging.getLogger().addHandler(handler)

    def run(self):
        parser = optparse.OptionParser()
        parser.add_option("-s", "--simulate", default=False, action="store_true")
        parser.add_option("-p", "--ypath", default=[], action="append")
        parser.add_option("", "--log-facility", default="2", help="the syslog local facility number to which to write the audit trail")
        parser.add_option("", "--log-level", default="info", help="the minimum log level to write to the audit trail")
        parser.add_option("-d", "--debug", default=False, help="switch all logging to maximum, and write out to the console")
        parser.add_option("-l", "--logfile", default=None, help="The filename to write the audit log to, instead of syslog. Note: the standard console log will still be written to the console.")
        parser.add_option("-v", "--verbose", default=0, action="count", help="Write additional informational messages to the console log. repeat for even more verbosity.")
        parser.add_option("-H", "--html", default=None, help="Instead of writing progress information to the console, write an html progress log to this file.")

        opts, args = parser.parse_args()
        if opts.debug:
            opts.html = False
            opts.logfile = "-"
            opts.verbose = 2
        self.configure_logging(opts)
        ctx = RunContext(opts)
        config = yay.load_uri(args[0])
        self.resources = resource.ResourceBundle(config.get("resources", []))
        self.resources.bind()
        shell = Shell(ctx, change.ChangeLog(ctx), simulate=opts.simulate)
        self.resources.apply(shell, config)
        return 0

def main():
    return Runner().run()

