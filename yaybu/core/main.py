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

import os
import optparse
import yay
from yaybu.core import runner, remote, runcontext
import logging, atexit

def version():
    import pkg_resources

    yaybu_version = pkg_resources.get_distribution('Yaybu').version
    yay_version = pkg_resources.get_distribution('Yay').version
    return 'Yaybu %s\n' \
           'yay %s' % (yaybu_version, yay_version)

def main():
    parser = optparse.OptionParser(version=version())
    parser.add_option("-s", "--simulate", default=False, action="store_true")
    parser.add_option("-p", "--ypath", default=[], action="append")
    parser.add_option("", "--log-facility", default="2", help="the syslog local facility number to which to write the audit trail")
    parser.add_option("", "--log-level", default="info", help="the minimum log level to write to the audit trail")
    parser.add_option("-d", "--debug", default=False, action="store_true", help="switch all logging to maximum, and write out to the console")
    parser.add_option("-l", "--logfile", default=None, help="The filename to write the audit log to, instead of syslog. Note: the standard console log will still be written to the console.")
    parser.add_option("-v", "--verbose", default=2, action="count", help="Write additional informational messages to the console log. repeat for even more verbosity.")
    parser.add_option("--host", default=None, action="store", help="A host to remotely run yaybu on")
    parser.add_option("-u", "--user", default="root", action="store", help="User to attempt to run as")
    parser.add_option("--remote", default=False, action="store_true", help="Run yaybu.protocol client on stdio")
    parser.add_option("--ssh-auth-sock", default=None, action="store", help="Path to SSH Agent socket")
    parser.add_option("--expand-only", default=False, action="store_true", help="Set to parse config, expand it and exit")
    parser.add_option("--resume", default=False, action="store_true", help="Resume from saved events if terminated abnormally")
    parser.add_option("--no-resume", default=False, action="store_true", help="Clobber saved event files if present and do not resume")
    parser.add_option("--env-passthrough", default=[], action="append", help="Preserve an environment variable in any processes Yaybu spawns")
    opts, args = parser.parse_args()

    if len(args) != 1:
        parser.print_help()
        return 1

    if opts.debug:
        opts.logfile = "-"
        opts.verbose = 2

    if opts.expand_only:
        ctx = runcontext.RunContext(args[0], opts)
        cfg = ctx.get_config().get()

        if opts.verbose <= 2:
            cfg = dict(resources=cfg.get("resources", []))

        print yay.dump(cfg)
        return 0

    if opts.ssh_auth_sock:
        os.environ["SSH_AUTH_SOCK"] = opts.ssh_auth_sock

    atexit.register(logging.shutdown)

    # Probably not the best place to put this stuff...
    if os.path.exists("/etc/yaybu"):
        config = yay.load_uri("/etc/yaybu")
        opts.env_passthrough = config.get("env-passthrough", opts.env_passthrough)

    if opts.host:
        r = remote.RemoteRunner()
        r.load_system_host_keys()
        r.set_missing_host_key_policy("ask")
    else:
        r = runner.Runner()

    if not opts.remote:
        ctx = runcontext.RunContext(args[0], opts)
    else:
        ctx = runcontext.RemoteRunContext(args[0], opts)

    rv = r.run(ctx)
    return rv

