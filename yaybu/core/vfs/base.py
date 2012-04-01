
class Base(object):

    def __init__(self, ctx):
        self.context = ctx
        self.shell = ctx.shell
        self.simulate = ctx.simulate

    def exists(self, path):
        raise NotImplementedError(self.exists)

    def isfile(self, path):
        raise NotImplementedError(self.isfile)

    def isdir(self, path):
        raise NotImplementedError(self.isdir)

    def islink(self, path):
        raise NotImplementedError(self.islink)

    def stat(self, path):
        raise NotImplementedError(self.stat)

    def open(self, path, mode, fsmode=None):
        raise NotImplementedError(self.open)

    def delete(self, path):
        self.shell.execute(["/bin/rm", path])

