
import os
import tempfile
import subprocess
import urllib2

import logging

logger = logging.getLogger("cloudinit")

class CloudInitException(Exception):

    def __init__(self, message, log=""):
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

class RemoteUbuntuCloudImage:

    server = "cloud-images.ubuntu.com"
    source = "http://{server}/releases/{release}/release"
    filename = "ubuntu-{release}-server-cloudimg-{arch}.{extension}"
    blocksize = 81920

    def __init__(self, directory, release="13.10", arch="amd64"):
        """ Specify a local filename which will be overwritten if missing our out of date """
        self.directory = directory
        self.release = release
        self.arch = arch

    def remote_url(self, extension):
        urlpattern = self.remote + "/" + self.filename

    def fetch(self, extension):
        args = dict(server=self.server, release=self.release, arch=self.arch, extension=extension)
        source = self.source.format(**args)
        filename = self.filename.format(**args)
        remote_url = source + "/" + filename
        try:
            response = urllib2.urlopen(remote_url)
        except urllib2.HTTPError:
            raise CloudInitException("Unable to fetch {0}".format(remote_url))
        local = open(os.path.join(self.directory, filename), "w")
        while True:
            data = response.read(self.blocksize)
            if not data:
                break
            local.write(data)

class CloudInit:

    def __init__(self, directory, release="13.10", arch="amd64"):
        self.directory = directory
        self.release = release
        self.arch = arch

    def create_seed(self):
        """ Create a seed ISO image in the specified filename """
        s = Seed(os.path.join(self.directory, "seed.iso"))
        s.update()
        s.save()
        s.cleanup()

    def fetch_image(self):
        r = RemoteUbuntuCloudImage(self.directory)
        r.fetch("tar.gz")
        r.fetch("ovf")


if __name__ == "__main__":
    cloudinit = CloudInit(".")
    cloudinit.create_seed()
    cloudinit.fetch_image()

# create the seed iso image
# fetch the image from the ubuntu cloud website
# fetch the ovf as well
# convert the image into a vmdk
# attach seed.iso
# boot with ds=nocloud-net parameter to kernel
# make changes to the image so it knows it is not on EC2
