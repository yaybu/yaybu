import os
import posix
import grp
import pwd
import spwd

from yaybu.core.error import SystemError
from .base import Base


class Shell(Base):

    def exists(self, path):
        return self.shell._execute(["test", "-e", path], None)[0] == 0

    def isfile(self, path):
        return self.shell._execute(["test", "-f", path], None)[0] == 0

    def isdir(self, path):
        return self.shell._execute(["test", "-d", path], None)[0] == 0

    def islink(self, path):
        return self.shell._execute(["test", "-L", path], None)[0] == 0

    def stat(self, path):
        data = self.shell._execute(["stat", "-L", "-t", path], None)[1].split(" ")
        return posix.stat_result((
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
            ))

    def lstat(self, path):
        data = self.shell._execute(["stat", "-t", path], None)[1].split(" ")
        return posix.stat_result((
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
            ))

    def lexists(self, path):
        # stat command uses lstat syscall by default
        return self.shell._execute(["stat", path], None)[0] == 0

    def readlink(self, path):
        try:
            link = self.shell._execute(["readlink", path], None)[1].split("\n")[0].strip()
            return link
        except SystemError:
            raise OSError

    def open(self, path, mode, fsmode=None):
        return open(path, mode)

    def get(self, path):
        return self.shell._execute(["cat", path], None)[1]

    def put(self, path, contents, chmod=0o644):
        umask = 0o777 - chmod
        return self.shell._execute("umask %o && tee %s > /dev/null" % (umask, path), None, stdin=contents)

    def makedirs(self, path):
        return self.shell.execute(["mkdir", "-p", path], None)

    def getgrall(self):
        groups = self.get("/etc/group")
        for line in groups.split("\n"):
            if not line.strip():
                continue
            tup = line.split(":")
            yield grp.struct_group((
                tup[0],
                tup[1],
                int(tup[2]),
                tup[3].split(","),
                ))

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
            yield pwd.struct_passwd((
                tup[0],
                tup[1],
                int(tup[2]),
                int(tup[3]),
                tup[4],
                tup[5],
                tup[6]
                ))

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
            yield spwd.struct_spwd(line.split(":"))

    def getspnam(self, name):
        for suser in self.getspall():
            if suser.sp_nam == name:
                return suser
        raise KeyError(name)

