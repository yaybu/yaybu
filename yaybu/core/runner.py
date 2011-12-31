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
import sys
import logging
import logging.handlers
import subprocess
import getpass

from yaybu.core import error
from yaybu.core import runcontext
from yaybu.core import event

logger = logging.getLogger("runner")

class LoaderError(Exception):
    pass


class Runner(object):

    def trampoline(self, username):
        command = ["sudo", "-u", username] + sys.argv[0:1]

        if "SSH_AUTH_SOCK" in os.environ:
            command.extend(["--ssh-auth-sock", os.environ["SSH_AUTH_SOCK"]])

        command.extend(sys.argv[1:])

        os.execvp(command[0], command)

    def run(self, ctx, bundle=None):
        """ Run locally. """
        if ctx.user and getpass.getuser() != ctx.user:
            self.trampoline(ctx.user)
            return 0

        event.EventState.save_file = "/var/run/yaybu/events.saved"

        # This makes me a little sad inside, but the whole
        # context thing needs a little thought before jumping in
        event.state.simulate = ctx.simulate

        if not ctx.simulate:
            save_parent = os.path.realpath(os.path.join(event.EventState.save_file, os.path.pardir))
            if not os.path.exists(save_parent):
                os.mkdir(save_parent)

        try:
            if os.path.exists(event.EventState.save_file):
                if ctx.resume:
                    event.state.loaded = False
                elif ctx.no_resume:
                    if not ctx.simulate:
                        os.unlink(event.EventState.save_file)
                    event.state.loaded = True
                else:
                    raise error.SavedEventsAndNoInstruction("There is a saved events file - you need to specify --resume or --no-resume")

            # FIXME: We can pull this out to somewhere nicer now
            if bundle:
                ctx.set_bundle(bundle)

            # Actually apply the configuration
            changed = ctx.get_bundle().apply(ctx, ctx.get_config())

            if not ctx.simulate and os.path.exists(event.EventState.save_file):
                os.unlink(event.EventState.save_file)

            if not changed:
                # nothing changed
                ctx.changelog.info("No changes were required")
                return 254

            ctx.changelog.info("All changes were applied successfully")
            return 0

        except error.ExecutionError, e:
            # this will have been reported by the context manager, so we wish to terminate
            # but not to raise it further. Other exceptions should be fully reported with
            # tracebacks etc automatically
            ctx.changelog.error("Terminated due to execution error in processing")
            return e.returncode
        except error.Error, e:
            # If its not an Execution error then it won't have been logged by the
            # Resource.apply() machinery - make sure we log it here.
            ctx.changelog.write(str(e))
            ctx.changelog.error("Terminated due to error in processing")
            return e.returncode
        except SystemExit:
            # A normal sys.exit() is fine..
            raise
        #except:
        #    from yaybu.core.debug import post_mortem
        #    post_mortem()
        #    raise

