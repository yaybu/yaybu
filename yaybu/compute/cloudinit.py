
import os
import tempfile
import subprocess
import urllib2
#import xml.etree.ElementTree as ET
import lxml.etree as ET
import hashlib

import logging

logger = logging.getLogger("cloudinit")

import wingdbstub

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
        print >> f, "instance-id: foo1"

    def create_user_data(self):
        f = self.open("user-data", "w")
        print >> f, "#cloud-config"
        print >> f, "password: password"
        print >> f, "chpasswd: { expire: False }"

    def update(self):
        for f in self.filenames:
            fn = "create_" + f.replace("-", "_")
            getattr(self, fn)()
        self.save()

    def cleanup(self):
        for f in self.filenames:
            os.unlink(os.path.join(self.tmpdir, f))
        os.rmdir(self.tmpdir)

class UbuntuCloudImage:

    server = "cloud-images.ubuntu.com"
    source = "http://{server}/releases/{release}/release"
    fn_pattern = "ubuntu-{release}-server-cloudimg-{arch}{extension}"
    extensions = ['-disk1.img', '.ovf']
    xmlns = {"env": "http://schemas.dmtf.org/ovf/envelope/1"}
    blocksize = 81920

    def __init__(self, directory, release="13.10", arch="amd64"):
        """ Specify a local filename which will be overwritten if missing our out of date """
        self.directory = directory
        self.release = release
        self.arch = arch

    def filename(self, extension):
        return self.fn_pattern.format(**self.fmt_args(extension))

    def fmt_args(self, extension):
        return dict(server=self.server,
                    release=self.release,
                    arch=self.arch,
                    extension=extension)

    def fetch(self, extension):
        import wingdbstub
        args = self.fmt_args(extension)
        source = self.source.format(**args)
        filename = self.filename(extension)
        remote_url = source + "/" + filename
        try:
            response = urllib2.urlopen(remote_url)
        except urllib2.HTTPError:
            print remote_url
            raise CloudInitException("Unable to fetch {0}".format(remote_url))
        local = open(os.path.join(self.directory, filename), "w")
        while True:
            data = response.read(self.blocksize)
            if not data:
                break
            local.write(data)

    def get_remote_sums(self):
        logger.debug("Fetching remote image sums")
        remote_url = self.source.format(**self.fmt_args("")) + "/SHA1SUMS"
        response = urllib2.urlopen(remote_url)
        sums = {}
        for line in response:
            line = line.strip()
            s, f = line.split()
            sums[f[1:]] = s
        return sums

    def get_local_sums(self):
        sums = {}
        for e in self.extensions:
            filename = self.filename(e)
            pathname = os.path.join(self.directory, filename)
            h = hashlib.sha1()
            if os.path.exists(pathname):
                h.update(open(pathname).read())
                sums[filename] = h.hexdigest()
        return sums

    def update(self):
        remote = self.get_remote_sums()
        local = self.get_local_sums()
        for e in self.extensions:
            filename = self.filename(e)
            logger.debug("Checking sums for {0}".format(filename))
            if filename not in remote:
                logger.info("Remote sum missing for {0}, fetching".format(filename))
                self.fetch(e)
            elif filename not in local:
                logger.info("{0} not present locally, fetching".format(filename))
                self.fetch(e)
            elif local[filename] != remote[filename]:
                logger.info("Local {0} does not match remote sum, fetching".format(filename))
                self.fetch(e)
            else:
                logger.info("Sums match for {0}".format(filename))
        # TODO check sums subsequently

    def read_vmx_config(self):
        config = {}
        vmx = os.path.join(self.directory, self.filename(".vmx"))
        for l in open(vmx):
            l = l.strip()
            name, value = l.split("=", 1)
            config[name] = value
        return config

    def write_vmx_config(self, config):
        vmx = os.path.join(self.directory, self.filename(".vmx"))
        f = open(vmx, "w")
        for name, value in config.items():
            print >> f, "{0} = {1}".format(name, value)

    def make_vmx(self):
        self.convert_image()
        self.convert_ovf()
        command = [
            "ovftool",
            "-o",
            self.filename(".ovf"),
            self.filename(".vmx"),
        ]
        logger.info("Converting to VMX")
        logger.debug("Executing {0}".format(" ".join(command)))
        p = subprocess.Popen(
            args=command,
            stdin=None,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=self.directory
        )
        stdout, stderr = p.communicate()
        if p.returncode != 0:
            logger.debug(stdout)
            logger.debug(stderr)
            raise CloudInitException("ovftool failed")
        config = self.read_vmx_config()
        for n in config.keys():
            if n.startswith("ide"):
                del config[n]
        config.update({
            "ide0:0.present": "TRUE",
            "ide0:0.fileName":  "seed.iso",
            "ide0:0.deviceType": "cdrom-image",
        })
        self.write_vmx_config(config)

    def convert_image(self):
        filename = self.filename("-disk1.img")
        destination = "disk1.vmdk"
        command = [
            "qemu-img",
            "convert",
            "-O", "vmdk",
            os.path.join(self.directory, filename),
            os.path.join(self.directory, destination),
        ]
        logger.info("Converting image to vmdk format")
        logger.debug("Executing {0}".format(" ".join(command)))
        p = subprocess.Popen(
            args=command,
            stdin=None,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout, stderr = p.communicate()
        if p.returncode != 0:
            raise CloudInitException("qemu-img failed", log=stdout+stderr)

    def convert_ovf(self):
        filename = os.path.join(self.directory, self.filename(".ovf"))
        disk_image = os.path.join(self.directory, "disk1.vmdk")
        image_size = len(open(disk_image).read())
        tree = ET.parse(filename)
        disk = tree.find("./env:References/env:File", self.xmlns)
        disk.attrib["{%s}size" % self.xmlns["env"]] = str(image_size)
        disk.attrib["{%s}href" % self.xmlns["env"]] = "disk1.vmdk"
        product_section = tree.find("./env:VirtualSystem/env:ProductSection", namespaces=self.xmlns)
        for elem in product_section.findall("env:Property", namespaces=self.xmlns):
            product_section.remove(elem)
        tree.write(filename)

class CloudInit:

    def __init__(self, directory, release="13.10", arch="amd64"):
        self.directory = os.path.realpath(directory)
        self.release = release
        self.arch = arch

    def create_seed(self):
        """ Create a seed ISO image in the specified filename """
        s = Seed(os.path.join(self.directory, "seed.iso"))
        s.update()
        s.save()
        s.cleanup()

    def fetch_image(self):
        r = UbuntuCloudImage(self.directory)
        r.update()
        r.make_vmx()

if __name__ == "__main__":
    import sys
    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
    if not os.path.exists("cloudinit"):
        os.mkdir("cloudinit")
    cloudinit = CloudInit("cloudinit")
    cloudinit.create_seed()
    cloudinit.fetch_image()

# create the seed iso image
# fetch the image from the ubuntu cloud website
# fetch the ovf as well
# convert the image into a vmdk
# attach seed.iso
# boot with ds=nocloud-net parameter to kernel
# make changes to the image so it knows it is not on EC2
