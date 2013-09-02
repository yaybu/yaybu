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
import signal
import socket

from yaybu import util


gpg_agent_pid = None


def setup_gpg_agent():
    global gpg_agent_pid

    if "GPG_AGENT_INFO" in os.environ:
        return

    if not util.is_mac_bundle():
        return

    socket_path = os.path.expanduser("~/.gnupg/S.gpg-agent")
    if os.path.exists(socket_path):
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            s.connect(socket_path)
        except socket.error as e:
            if e.errno != 61:
                # gpg-agent is already running
                return
        else:
            return

    path = util.get_bundle_path("Resources/bin/gpg-agent")
    pinentry = util.get_bundle_path("Resources/libexec/pinentry-mac.app/Contents/MacOS/pinentry-mac")

    # Starting gpg-agent on a fresh computer causes us to hang!
    # Precreating .gnupg seems to 'fix' it...
    def ensure_directory(path, mode=0700):
        if not os.path.exists(path):
            os.makedirs(path)
            os.chmod(path, mode)
    ensure_directory(os.path.expanduser("~/.gnupg"))
    ensure_directory(os.path.expanduser("~/.gnupg/private-keys-v1.d"))

    import subprocess
    p = subprocess.Popen([path, "--daemon", "--sh", "--pinentry-program", pinentry], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()
    os.environ["GPG_AGENT_INFO"] = GPG_AGENT_INFO = stdout.strip().rsplit(";", 1)[0].split("=", 1)[1]
    sock, pid, umm = GPG_AGENT_INFO.split(":")
    gpg_agent_pid = int(pid)


def teardown_gpg_agent():
    if not gpg_agent_pid is None:
        os.kill(gpg_agent_pid, signal.SIGKILL)
        del os.environ["GPG_AGENT_INFO"]


if __name__ == "__main__":
    main()

