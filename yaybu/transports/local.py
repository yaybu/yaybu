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
try:
    import spwd
except ImportError:
    spwd = None
import shlex
import pipes

from yay import String

from ..core import error
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


class LocalTransport(base.Transport):

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

    def execute(self, command, user="root", group=None, stdin=None, env=None, shell=False, cwd=None, umask=None, expected=0, stdout=None, stderr=None):
        if not user:
            user = pwd.getpwuid(os.getuid()).pw_name

        newenv = {}
        if self.env_passthrough:
            for var in self.env_passthrough:
                if var in os.environ:
                    newenv[var] = os.environ[var]
        
        newenv.update({
            #"HOME": "/home/" + self.user,
            "LOGNAME": user,
            "PATH": "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
            "SHELL": "/bin/sh",
            })

        if env:
            newenv.update(env)

        def preexec():
            if group:
                try:
                    gid = grp.getgrnam(group).gr_gid
                except KeyError:
                    raise error.InvalidGroup("No such group '%s'" % group)
                if gid != os.getgid():
                    os.setgid(gid)
                if gid != os.getegid():
                    os.setegid(gid)

            if user:
                try:
                    uid = pwd.getpwnam(user).pw_uid
                except KeyError:
                    raise error.InvalidUser("No such user '%s'" % user)
                if uid != os.getuid():
                    os.setuid(uid)
                if uid != os.geteuid():
                    os.seteuid(uid)

            if umask:
                os.umask(umask)

        p = subprocess.Popen(command,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             cwd=cwd or "/",
                             env=newenv,
                             preexec_fn=preexec,
                             )
        returncode, stdout, stderr = self.communicate(p, stdout, stderr)
        return returncode, stdout, stderr

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
        fd = os.open(path, os.O_WRONLY|os.O_CREAT|os.O_SYNC|os.O_DIRECT, chmod)
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
