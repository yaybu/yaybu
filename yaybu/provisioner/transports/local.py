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

import subprocess
import os, select
try:
    import pwd
except ImportError:
    pass
try:
    import grp
except ImportError:
    pass
try:
    import spwd
except ImportError:
    spwd = None

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


class LocalExecute(object):

    def communicate(self, p, stdin=None, stdout_fn=None, stderr_fn=None):
        if p.stdin:
            if stdin:
                p.stdin.write(stdin)
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

    def _execute(self, command, stdin=None, stdout=None, stderr=None):
        #print command
        p = subprocess.Popen(command,
                             stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             cwd="/tmp",
                             env=self.env,
                             )
        returncode, stdout, stderr = self.communicate(p, stdin, stdout, stderr)
        #print ">>", returncode
        #print ">>", stdout
        #print ">>", stderr
        return returncode, stdout, stderr


class LocalTransport(LocalExecute, base.Transport):

    def whoami(self):
        return pwd.getpwuid(os.getuid()).pw_name

    def exists(self, path):
        return os.path.exists(path)

    def isfile(self, path):
        return os.path.isfile(path)

    def isdir(self, path):
        return os.path.isdir(path)

    def islink(self, path):
        return os.path.islink(path)

    def stat(self, path):
        return os.stat(path)

    def lexists(self, path):
        return os.path.lexists(path)

    def readlink(self, path):
        return os.readlink(path)

    def lstat(self, path):
        return os.lstat(path)

    def get(self, path):
        return open(path).read()

    def put(self, path, contents, chmod=0o644):
        fd = os.open(path, os.O_WRONLY|os.O_CREAT|os.O_SYNC, chmod)
        os.write(fd, contents)
        os.close(fd)

    def makedirs(self, path):
        os.makedirs(path)

    def unlink(self, path):
        os.unlink(path)

    def getgrall(self):
        return grp.getgrall()

    def getgrnam(self, name):
        return grp.getgrnam(name)

    def getgrgid(self, gid):
        return grp.getgrgid(gid)

    def getpwall(self):
        return pwd.getpwall()

    def getpwnam(self, name):
        return pwd.getpwnam(name)

    def getpwuid(self, uid):
        return pwd.getpwuid(uid)

    def getspall(self):
        return spwd.getspall()

    def getspnam(self, name):
        return spwd.getspnam(name)


