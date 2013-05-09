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

import os
import pipes
import select
import collections

import paramiko

from yay import String

from ..core import error
from . import base


stat_result = collections.namedtuple("stat_result", \
    ("st_mode", "st_ino", "st_dev", "st_nlink", "st_uid", "st_gid", \
    "st_size", "st_atime", "st_mtime", "st_ctime"))

struct_group = collections.namedtuple("struct_group", \
    ("gr_name", "gr_passwd", "gr_gid", "gr_mem"))

struct_passwd = collections.namedtuple("struct_passwd", \
    ("pw_name", "pw_passwd", "pw_uid", "pw_gid", "pw_gecos", "pw_dir", \
    "pw_shell"))

struct_spwd = collections.namedtuple("struct_spwd", \
    ("sp_nam", "sp_pwd", "sp_lastchg", "sp_min", "sp_max", "sp_warn", \
    "sp_inact", "sp_expire", "sp_flag", ))


class RemoteTransport(base.Transport):

    connection_attempts = 10
    missing_host_key_policy = paramiko.AutoAddPolicy()
    key = None
    _client = None

    def connect(self):
        if self._client:
            return self._client

        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(self.missing_host_key_policy)
        for tries in range(self.connection_attempts):
            try:
                if self.key is not None:
                    client.connect(hostname=self.context.host,
                                   username=self.context.connect_user or "ubuntu",
                                   port=self.context.port or 22,
                                   pkey=self.key,
                                   look_for_keys=False)
                else:
                    client.connect(hostname=self.context.host,
                                   username=self.context.connect_user or "ubuntu",
                                   port=self.context.port or 22,
                                   look_for_keys=True)
                break

            except paramiko.PasswordRequiredException:
                raise error.ConnectionError("Unable to authenticate with remote server")

            except (socket.error, EOFError):
                # logger.warning("connection refused. retrying.")
                time.sleep(tries + 1)
        else:
            client.close()
            raise error.ConnectionError("Connection refused %d times, giving up." % self.connection_attempts)
        self._client = client
        return client

    def _refresh_intel(self):
        """ Thinking we grab env, users, groups, etc so we can do extra pre-validation... """
        pass

    def execute(self, command, user="root", group=None, stdin=None, env=None, shell=False, cwd=None, umask=None, expected=0, stdout=None, stderr=None):
        client = self.connect() # This should be done once per context object
        transport = client.get_transport()

        # No need to change user if we are already the right one
        if user == transport.get_username():
            user = None

        full_command = []
        if user or group:
            full_command.append('sudo')
        if user:
            full_command.extend(['-u', user])
        if group:
            full_command.extend(['-g', group])

        if isinstance(command, list):
            command = " ".join([pipes.quote(c) for c in command])

        if env:
            vars = []
            for k, v in env.items():
                vars.append("%s=%s" % (k, pipes.quote(v)))
            command = "export " + " ".join(vars) + "; " + command
            full_command.extend(["env", "-"])

        full_command.extend(["sh", "-c", command])

        # print ' '.join([pipes.quote(c) for c in full_command])

        channel = transport.open_session()
        channel.exec_command(' '.join([pipes.quote(c) for c in full_command]))

        if stdin:
            channel.send(stdin)
            channel.shutdown_write()

        stdout_buffer = ""
        while not channel.exit_status_ready():
            rlist, wlist, xlist = select.select([channel], [], [])
            if not rlist:
                continue
            data = channel.recv(1024)
            if data:
                if stdout:
                    stdout(data)
                stdout_buffer += data

        while channel.recv_ready():
            data = channel.recv(1024)
            if data:
                if stdout:
                    stdout(data)
                stdout_buffer += data

        returncode = channel.recv_exit_status()
        return returncode, stdout_buffer, ''

    def exists(self, path):
        return self.execute(["test", "-e", path])[0] == 0

    def isfile(self, path):
        return self.execute(["test", "-f", path])[0] == 0

    def isdir(self, path):
        return self.execute(["test", "-d", path])[0] == 0

    def islink(self, path):
        return self.execute(["test", "-L", path])[0] == 0

    def stat(self, path):
        data = self.execute(["stat", "-L", "-t", path])[1].split(" ")
        return stat_result(
            int(data[3], 16), # st_mode
            int(data[8]), #st_ino
            int(data[7], 16), #st_dev
            int(data[9]), # st_nlink
            int(data[4]), # st_uid
            int(data[5]), # st_gid
            int(data[1]), # st_size
            int(data[11]), # st_atime
            int(data[12]), # st_mtime
            int(data[13]), # st_ctime
            )

    def lstat(self, path):
        data = self.execute(["stat", "-t", path])[1].split(" ")
        return stat_result(
            int(data[3], 16), # st_mode
            int(data[8]), #st_ino
            int(data[7], 16), #st_dev
            int(data[9]), # st_nlink
            int(data[4]), # st_uid
            int(data[5]), # st_gid
            int(data[1]), # st_size
            int(data[11]), # st_atime
            int(data[12]), # st_mtime
            int(data[13]), # st_ctime
            )

    def lexists(self, path):
        # stat command uses lstat syscall by default
        return self.execute(["stat", path])[0] == 0

    def readlink(self, path):
        try:
            link = self.execute(["readlink", path])[1].split("\n")[0].strip()
            return link
        except SystemError:
            raise OSError

    def get(self, path):
        return self.execute(["cat", path])[1]

    def put(self, path, contents, chmod=0o644):
        umask = 0o777 - chmod
        return self.execute("umask %o && tee %s > /dev/null" % (umask, path), stdin=contents)

    def makedirs(self, path):
        return self.execute(["mkdir", "-p", path])

    def unlink(self, path):
        return self.execute(["rm", "-f", path])

    def getgrall(self):
        groups = self.get("/etc/group")
        for line in groups.split("\n"):
            if not line.strip():
                continue
            tup = line.split(":")
            yield struct_group(
                tup[0],
                tup[1],
                int(tup[2]),
                tup[3].split(","),
                )

    def getgrnam(self, name):
        for group in self.getgrall():
            if group.gr_name == name:
                return group
        raise KeyError(name)

    def getgrgid(self, gid):
        for group in self.getgrall():
            if gr.gr_gid == gid:
                return group
        raise KeyError(gid)

    def getpwall(self):
        users = self.get("/etc/passwd")
        for line in users.split("\n"):
            if not line.strip():
                continue
            tup = line.split(":")
            yield struct_passwd(
                tup[0],
                tup[1],
                int(tup[2]),
                int(tup[3]),
                tup[4],
                tup[5],
                tup[6]
                )

    def getpwnam(self, name):
        for user in self.getpwall():
            if user.pw_name == name:
                return user
        raise KeyError(name)

    def getpwuid(self, uid):
        for user in self.getpwall():
            if user.pw_uid == uid:
                return user
        raise KeyError(uid)

    def getspall(self):
        susers = self.get("/etc/shadow")
        for line in susers.split("\n"):
            if not line.strip():
                continue
            yield struct_spwd(*line.split(":"))

    def getspnam(self, name):
        for suser in self.getspall():
            if suser.sp_nam == name:
                return suser
        raise KeyError(name)
