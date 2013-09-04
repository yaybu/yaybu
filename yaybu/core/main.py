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

usage = """usage: %prog [options] [command]
when run without any commands yaybu drops to a command prompt.
for more information on a command:
    %prog [command] -h
"""

def _main():
    # We do the imports here so that Ctrl+C doesn't show any ugly traceback
    import os
    import sys
    import optparse
    import logging, atexit
    import signal

    from yaybu import util
    from yaybu.core.util import version
    from yaybu.core import command

    parser = optparse.OptionParser(version=version(), usage=usage)
    parser.disable_interspersed_args()
    parser.add_option("-p", "--ypath", default=[], action="append")
    parser.add_option("", "--log-facility", default="2", help="the syslog local facility number to which to write the audit trail")
    parser.add_option("", "--log-level", default="info", help="the minimum log level to write to the audit trail")
    parser.add_option("-d", "--debug", default=False, action="store_true", help="switch all logging to maximum, and write out to the console")
    parser.add_option("-l", "--logfile", default=None, help="The filename to write the audit log to, instead of syslog. Note: the standard console log will still be written to the console.")
    parser.add_option("-v", "--verbose", default=2, action="count", help="Write additional informational messages to the console log. repeat for even more verbosity.")
    parser.add_option("-C", "--config", default=None, action="store", help="Path to main yay config file")
    opts, args = parser.parse_args()

    # we need to revisit how logging is handled
    logging.basicConfig(format="%(asctime)s %(name)s %(levelname)s %(message)s")
    if opts.debug:
        root = logging.getLogger()
        root.setLevel(logging.DEBUG)
        opts.logfile = "-"
        opts.verbose = 2

    if sys.platform == "darwin":
        # CA certs on darwin are in the system keyring - they can be readily accessed with commands like:
        #   security export -k /System/Library/Keychains/SystemCACertificates.keychain -t certs
        # However i'm not sure how libcloud/python can take a stream of certs - it looks like the certs have to exist on disk!!
        # For now, turning cert verification off on Macs.
        import libcloud.security
        libcloud.security.VERIFY_SSL_CERT = False
        libcloud.security.VERIFY_SSL_CERT_STRICT = False


    logging.getLogger("paramiko.transport").setLevel(logging.CRITICAL)

    atexit.register(logging.shutdown)

    com = command.YaybuCmd(config=opts.config, verbose=opts.verbose, ypath=opts.ypath, logfile=opts.logfile, debug=opts.debug)

    if args:
        com.interactive_shell = False
        sys.exit(com.onecmd(" ".join(args)) or 0)
    else:
        com.cmdloop()


def main():
    try:
        _main()
    except KeyboardInterrupt:
        print ""


if __name__ == "__main__":
    main()

