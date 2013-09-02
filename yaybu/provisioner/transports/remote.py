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

"""
A mixin for remote transports that are based on the execute of shell commands -
for example, ssh or fakechroot
"""

import collections


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


class RemoteTransport(object):

    def exists(self, path):
        return self.execute(["test", "-e", path])[0] == 0

    def isfile(self, path):
        return self.execute(["test", "-f", path])[0] == 0

    def isdir(self, path):
        return self.execute(["test", "-d", path])[0] == 0

    def islink(self, path):
        return self.execute(["test", "-L", path])[0] == 0

    def stat(self, path):
        returncode, stdout, stderr = self.execute(["stat", "-L", "-t", path])
        if returncode != 0:
            raise OSError
        data = stdout.split(" ")
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
        returncode, stdout, stderr = self.execute(["stat", "-t", path])
        if returncode != 0:
            raise OSError
        data = stdout.split(" ")
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
        returncode, stdout, stderr = self.execute(["readlink", path])
        if returncode != 0:
            raise OSError
        return stdout.split("\n")[0].strip()

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
