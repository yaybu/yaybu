import os
import tempfile
import subprocess
import urllib2
import hashlib
import logging

from abc import ABCMeta, abstractmethod, abstractproperty

logger = logging.getLogger("cloudinit")


class CloudInitException(Exception):

    def __init__(self, message, log=""):
        self.message = message
        self.log = log


class FetchFailedException(CloudInitException):
    pass


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
            raise CloudInitException("genisoimage failed", log=stdout + stderr)

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


class ImageConverter:
    xmlns = {"env": "http://schemas.dmtf.org/ovf/envelope/1"}

    def __init__(self, directory):
        self.directory = directory

    def convert_image(self, source, destination, format):
        command = [
            "qemu-img",
            "convert",
            "-O", format,
            source,
            destination,
        ]
        logger.info("Converting image to {0} format".format(format))
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
            raise CloudInitException("qemu-img failed", log=stdout + stderr)

    def read_vmx_config(self, vmx):
        config = {}
        for l in open(os.path.join(self.directory, vmx)):
            l = l.strip()
            name, value = l.split("=", 1)
            config[name] = value
        return config

    def write_vmx_config(self, vmx, config):
        f = open(os.path.join(self.directory, vmx), "w")
        for name, value in config.items():
            print >> f, '{0} = "{1}"'.format(name, value)

    def create_plain_vmx(self, vmx, vmdk, name="New Machine"):
        config = {
            "displayname": name,
            "annotation": "Created by Yaybu.",
            "guestos": "fedora",
            "config.version": "8",
            "virtualhw.version": "7",
            ".encoding": "UTF-8",

            "memsize": "256",
            "cpuid.coresPerSocket": "1",
            "numvcpus": "1",

            "ethernet0.connectionType": "bridged",
            "ethernet0.present": "TRUE",
            "ethernet0.virtualDev": "e1000",
            "ethernet0.startConnected": "TRUE",
            "ethernet0.addressType": "generated",

            "scsi0.virtualDev": "lsilogic",
            "scsi0.present": "TRUE",
            "scsi0:0.present": "TRUE",
            "scsi0:0.fileName": vmdk,
            "scsi0:0.mode": "persistent",
            "scsi0:0.deviceType": "disk",

            "ide0:0.deviceType": "cdrom-image",
            "ide0:0.present": "TRUE",
            "ide0:0.fileName": "seed.iso",

            "usb.present": "TRUE",
            "floppy0.present": "FALSE",
            "vmci0.present": "TRUE",

            "toolscripts.afterresume": "true",
            "toolscripts.afterpoweron": "true",
            "toolscripts.beforesuspend": "true",
            "toolscripts.beforepoweroff": "true",

            "pciBridge0.present": "TRUE",
            "pciBridge4.present": "TRUE",
            "pciBridge5.present": "TRUE",
            "pciBridge6.present": "TRUE",
            "pciBridge7.present": "TRUE",
            "pciBridge4.virtualDev": "pcieRootPort",
            "pciBridge5.virtualDev": "pcieRootPort",
            "pciBridge6.virtualDev": "pcieRootPort",
            "pciBridge7.virtualDev": "pcieRootPort",
            "pciBridge4.functions": "8",
            "pciBridge5.functions": "8",
            "pciBridge6.functions": "8",
            "pciBridge7.functions": "8",
        }
        logger.info("Creating VMX file {0}".format(vmx))
        self.write_vmx_config(vmx, config)


class CloudImage(object):

    """ Represents a cloud image file for a specified release and
    architecture, with a local manifestation of the image. If no image exists
    locally it is fetched from the source provided by the distribution. e"""

    __metaclass__ = ABCMeta

    # size of blocks fetched from remote resources
    blocksize = 81920

    def __init__(self, directory, release, arch):
        self.directory = directory
        self.release = release
        self.arch = arch
        self.remote_hash = None
        self.local_hash = None

    @abstractproperty
    def hash_function(self):
        """ The hash function used to hash local files """

    @abstractmethod
    def remote_image_url(self):
        """ Return a complete url of the remote virtual machine image """

    @abstractmethod
    def remote_hashfile_url(self):
        """ Return a complete url of the remote hash file that contains the
        hash for the virtual machine image. Return None if no hash file is
        available. """

    @abstractmethod
    def filename_prefix(self):
        """ The first part of the filename, used for every file on disk
        locally, such as disk images, specification files, buffers etc.
        within the VM directory """

    @abstractmethod
    def image_hash(self, hashes):
        """ From the dictionary of all hashes provided in the remote hash
        file, return the hash of the virtual machine image """

    def local_filename(self, extension):
        return self.filename_prefix() + extension

    def local_pathname(self, extension):
        return os.path.join(self.directory, self.local_filename(extension))

    def local_image_filename(self):
        return self.local_filename(".img")

    def local_image_pathname(self):
        return self.local_pathname(".img")

    def fetch(self):
        remote_url = self.remote_image_url()
        pathname = self.local_image_pathname()
        logger.info("Retrieving {0} to {1}".format(remote_url, pathname))
        try:
            response = urllib2.urlopen(remote_url)
        except urllib2.HTTPError:
            raise CloudInitException("Unable to fetch {0}".format(remote_url))
        local = open(pathname, "w")
        while True:
            data = response.read(self.blocksize)
            if not data:
                break
            local.write(data)

    def decode_hashes(self, data):
        hashes = {}
        for line in data.splitlines():
            parts = line.strip().split()
            if len(parts) == 2:
                hashes[parts[1]] = parts[0]
        return hashes

    def get_remote_hashes(self):
        remote_url = self.remote_hashfile_url()
        logger.info("Fetching hashes from {0}".format(remote_url))
        try:
            response = urllib2.urlopen(remote_url)
        except urllib2.HTTPError:
            return {}
        return self.decode_hashes(response.read())

    def get_local_sum(self):
        pathname = self.local_image_pathname()
        h = self.hash_function()
        if os.path.exists(pathname):
            h.update(open(pathname).read())
            return h.hexdigest()

    def update_hashes(self):
        if self.remote_hash is None:
            self.remote_hash = self.image_hash(self.get_remote_hashes())
        self.local_hash = self.get_local_sum()

    def requires_update(self):
        if self.local_hash is None:
            logger.info("Image not present locally, fetching")
            return True
        elif self.local_hash != self.remote_hash:
            logger.info("Local image does not match remote sum, fetching")
            return True
        else:
            logger.info("Sums match for local image, not updating")
            return False

    def update(self):
        self.update_hashes()
        if self.requires_update():
            self.fetch()
        self.update_hashes()
        if self.requires_update():
            logger.error("Local image sum {0} does not match remote {1} after fetch.".format(self.local_hash, self.remote_hash))
            raise FetchFailedException("Local image missing or wrong after fetch")

    def make_vmx(self):
        source = self.local_image_filename()
        vmdk = self.local_filename(".vmdk")
        vmx = self.local_filename(".vmx")
        converter = ImageConverter(self.directory)
        converter.convert_image(source, vmdk, "vmdk")
        converter.create_plain_vmx(vmx, vmdk)


class StandardCloudImage(CloudImage):

    def remote_image_url(self):
        url = self.source + "/" + self.prefix + self.image_suffix
        return url.format(server=self.server,
                          release=self.release,
                          arch=self.arch)

    def remote_hashfile_url(self):
        url = self.source + "/" + self.checksums
        return url.format(server=self.server,
                          release=self.release,
                          arch=self.arch)

    def filename_prefix(self):
        return self.prefix.format(release=self.release, arch=self.arch)

    def image_hash(self, hashes):
        template = "*" + self.prefix + self.image_suffix
        filename = template.format(release=self.release, arch=self.arch)
        return hashes.get(filename, None)


class UbuntuCloudImage(StandardCloudImage):

    server = "cloud-images.ubuntu.com"
    source = "http://{server}/releases/{release}/release"
    prefix = "ubuntu-{release}-server-cloudimg-{arch}"
    image_suffix = "-disk1.img"
    checksums = "SHA256SUMS"
    hash_function = hashlib.sha256


class CirrosCloudImage(StandardCloudImage):

    server = "launchpad.net"
    source = "https://{server}/cirros/trunk/{release}/+download"
    prefix = "cirros-{release}-{arch}"
    image_suffix = "-disk.img"
    checksums = prefix + image_suffix + "/+md5"
    hash_function = hashlib.md5

    def image_hash(self, hashes):
        template = self.prefix + self.image_suffix
        filename = template.format(release=self.release, arch=self.arch)
        return hashes.get(filename, None)


class FedoraCloudImage(StandardCloudImage):

    """ Fedora images annoyingly have a version number in the remote
    filename, which can only be identified by inspecting the hash file. """

    server = "download.fedoraproject.org"
    source = "http://{server}/pub/fedora/linux/releases/{release}/Images/{arch}"
    checksums = "Fedora-Images-{arch}-{release}-CHECKSUM"
    prefix = "Fedora-{arch}-{release}"
    qcow = "Fedora-{arch}-{release}-{version}-sda.qcow2"
    hash_function = hashlib.sha256

    def update_hashes(self):
        if self.remote_hash is None:
            hashes = self.get_remote_hashes()
            self.find_version_in_hashes(hashes)
            self.remote_hash = self.image_hash(self.get_remote_hashes())
        self.local_hash = self.get_local_sum()

    def find_version_in_hashes(self, hashes):
        # this is mildly fugly, but the safest way of identifying the specific
        # version filename for this release
        for k in hashes:
            if k.endswith(".qcow2"):
                name, arch, release, version, tail = k.split("-")
                if arch == self.arch and release == self.release:
                    self.version = version
                    break

    def remote_image_url(self):
        # version is set as part of the hash retrieval phase
        url = self.source + "/" + self.qcow
        return url.format(server=self.server, release=self.release, arch=self.arch, version=self.version)

    def image_hash(self, hashes):
        filename = "*" + self.qcow.format(arch=self.arch, release=self.release, version=self.version)
        return hashes.get(filename, None)


class CloudInit:

    def __init__(self, directory, image):
        self.directory = directory
        self.image = image

    def create_seed(self):
        """ Create a seed ISO image in the specified filename """
        s = Seed(os.path.join(self.directory, "seed.iso"))
        s.update()
        s.save()
        s.cleanup()

    def fetch_image(self):
        self.image.update()
        self.image.make_vmx()

if __name__ == "__main__":
    import sys
    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
    directory = os.path.realpath("cloudinit")
    if not os.path.exists(directory):
        os.mkdir(directory)
    #image = UbuntuCloudImage(directory, "13.10", "amd64")
    image = FedoraCloudImage(directory, "20", "x86_64")
    image = CirrosCloudImage(directory, "0.3.0", "x86_64")
    cloudinit = CloudInit(directory, image)
    cloudinit.create_seed()
    cloudinit.fetch_image()
