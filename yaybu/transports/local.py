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

import logging
import subprocess
import os, getpass, pwd, grp, select
import shlex
import pipes

from yay import String

from . import error
from . import base


class Handle(object):

    def __init__(self, handle, callback=None):
        self.handle = handle
        self.callback = callback
        self._output = []

    def fileno(self):
        return self.handle.fileno()

    def read(self):
        data = os.read(self.fileno(), 1024)
        if data == "":
            self.handle.close()
            return False

        self._output.append(data)

        if self.callback:
            for l in data.splitlines():
                self.callback(l + "\r")

        return True

    def isready(self):
        return bool(self.handle)

    @property
    def output(self):
        out = ''.join(self._output)
        return out


class LocalShell(base.Shell):

    def communicate(self, p, stdout_fn=None, stderr_fn=None):
        if p.stdin:
            p.stdin.flush()
            p.stdin.close()

        stdout = Handle(p.stdout, stdout_fn)
        stderr = Handle(p.stderr, stderr_fn)

        # Initial readlist is any handle that is valid
        readlist = [h for h in (stdout, stderr) if h.isready()]

        while readlist:
            try:
                # Wait for data on stdout or stderr handles, but timeout after
                # one second so that we can poll (below) and check the process
                # hasn't disappeared.
                rlist, wlist, xlist = select.select(readlist, [], [], 1)
            except select.error, e:
                if e.args[0] == errno.EINTR:
                    continue
                raise

            # Some processes hang if we don't specifically poll for them going
            # away. We believe that under certain cases, child processes can
            # reuse their parent's file descriptors, and in that case, the
            # select loop will continue until the child process goes away, which
            # is undesirable when starting a daemon process.
            if not rlist and not wlist and not xlist:
                if p.poll() != None:
                    break

            # Read from all handles that select told us can be read from
            # If they return false then we are at the end of the stream
            # and stop reading from them
            for r in rlist:
                if not r.read():
                    readlist.remove(r)

        returncode = p.wait()

        return returncode, stdout.output, stderr.output

    def _execute(self, command, renderer):
        def preexec():
            if self.gid is not None:
                if self.gid != os.getgid():
                    os.setgid(self.gid)
                if self.gid != os.getegid():
                    os.setegid(self.gid)

            if self.uid is not None:
                if self.uid != os.getuid():
                    os.setuid(self.uid)
                if self.uid != os.geteuid():
                    os.seteuid(self.uid)

            if self.umask:
                os.umask(self.umask)

            os.environ.clear()
            os.environ.update(self._generated_env)

        try:
            p = subprocess.Popen(command,
                                 shell=self.shell,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 cwd=self.cwd,
                                 env=None,
                                 preexec_fn=preexec,
                                 )
            returncode, stdout, stderr = self.communicate(p, renderer.stdout, renderer.stderr)
            renderer.output(p.returncode)
            return returncode, stdout, stderr
        except Exception, e:
            renderer.exception(e)
            raise
