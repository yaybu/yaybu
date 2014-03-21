
import subprocess
import os
import logging

from . import error

logger = logging.getLogger("conversion")


class ImageConverter:

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
            raise error.CloudInitException("qemu-img failed", log=stdout + stderr)

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
