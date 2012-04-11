import os

from .base import Base


class Local(Base):

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

    def open(self, path, mode, fsmode=None):
        return open(path, mode)


