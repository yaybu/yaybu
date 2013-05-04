import os
import posix
from yaybu.core.error import SystemError
from .base import Base


class Shell(Base):

    def exists(self, path):
        return self.shell.execute(["test", "-e", path], inert=True, expected=None)[0] == 0

    def isfile(self, path):
        return self.shell.execute(["test", "-f", path], inert=True, expected=None)[0] == 0

    def isdir(self, path):
        return self.shell.execute(["test", "-d", path], inert=True, expected=None)[0] == 0

    def islink(self, path):
        return self.shell.execute(["test", "-L", path], inert=True, expected=None)[0] == 0

    def stat(self, path):
        data = self.shell.execute(["stat", "-t", path], inert=True)[1].split(" ")
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
        return self.shell.execute(["stat", path], inert=True, expected=None)[0] == 0

    def readlink(self, path):
        try:
            link = self.shell.execute(["readlink", path], inert=True)[1].split("\n")[0].strip()
            return link
        except SystemError:
            raise OSError

    def open(self, path, mode, fsmode=None):
        return open(path, mode)

    def get(self, path):
        return self.shell.execute(["cat", path], inert=True)[1]

    def put(self, path, contents):
        return self.shell.execute("tee %s > /dev/null" % path, inert=False, stdin=contents)

    def makedirs(self, path):
        return self.shell.execute(["mkdir", "-p", path], inert=False)
