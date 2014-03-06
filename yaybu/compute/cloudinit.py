
import os
import tempfile
import subprocess

import logging

logger = logging.getLogger("cloudinit")

class CloudInitException(Exception):

    def __init__(self, message, log):
        self.message = message
        self.log = log

class Seed:

    filenames = ['meta-data', 'user-data']

    def __init__(self, seedfile):
        self.seedfile = os.path.realpath(seedfile)
        self.tmpdir = tempfile.mkdtemp()

    def save(self):
        """ Overwrite the seed ISO file. Will clobber it potentially."""
        command = [
            "genisoimage",
            "-output", self.seedfile,
            "-volid", "cidata",
            "-joliet", "-rock",
            ]
        command.extend(self.filenames)
        p = subprocess.Popen(
            args=command,
            stdin=None,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=self.tmpdir
        )
        stdout, stderr = p.communicate()
        if p.returncode != 0:
            raise CloudInitException("genisoimage failed", log=stdout+stderr)


    def open(self, filename, mode):
        path = os.path.join(self.tmpdir, filename)
        return open(path, mode)

    def create_meta_data(self):
        f = self.open("meta-data", "w")
        print >> f, "local-hostname: localhost"

    def create_user_data(self):
        f = self.open("user-data", "w")
        print >> f, "#cloud-config"
        print >> f, "password: password"

    def update(self):
        for f in self.filenames:
            fn = "create_" + f.replace("-", "_")
            getattr(self, fn)()
        self.save()

    def cleanup(self):
        for f in self.filenames:
            os.unlink(os.path.join(self.tmpdir, f))
        os.rmdir(self.tmpdir)

class CloudInit:

    def __init__(self):
        pass

    def create_seed(self, filename):
        """ Create a seed ISO image in the specified filename """


if __name__ == "__main__":
    s = Seed("seed.iso")
    s.update()
    s.save()
    s.cleanup()

# create the seed iso image
# fetch the image from the ubuntu cloud website
# fetch the ovf as well
# convert the image into a vmdk
# attach seed.iso
# boot with ds=nocloud-net parameter to kernel
# make changes to the image so it knows it is not on EC2
