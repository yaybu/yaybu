import os

from .base import Base


class Shell(Base):

    def exists(self, path):
        return self.shell.execute(["test", "-e", path], inert=True)[0] == 0

    def isfile(self, path):
        return self.shell.execute(["test", "-f", path], inert=True)[0] == 0

    def isdir(self, path):
        return self.shell.execute(["test", "-d", path], inert=True)[0] == 0

    def islink(self, path):
        return self.shell.execute(["test", "-L", path], inert=True)[0] == 0

    def stat(self, path):
        return os.stat(path)

    def lexists(self, path):
        # stat command uses lstat syscall by default
        return self.shell.execute(["stat", path], inert=True)[0] == 0

    def readlink(self, path):
        return self.shell.execute(["readlink", path], inert=True)[1].split("\n")[0].strip()

    def open(self, path, mode, fsmode=None):
        return open(path, mode)


