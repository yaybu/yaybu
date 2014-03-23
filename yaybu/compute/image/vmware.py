# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import subprocess
import os
import logging
import random

from . import error
from . import cloudinit

logger = logging.getLogger("vmware")

def qemu_img(source, destination, format):
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
    )
    stdout, stderr = p.communicate()
    if p.returncode != 0:
        raise error.ImageConversionError("qemu-img failed", log=stdout + stderr)


class VMX(dict):

    def __init__(self, directory, prefix):
        self.directory = directory
        self.prefix = prefix
        if os.path.exists(self.vmx_pathname):
            self.read()
        else:
            self.create()
            self.write()

    @property
    def vmx_pathname(self):
        return os.path.join(self.directory, self.prefix+".vmx")

    def create(self):
        """ Create an empty vmx """
        self.update(self.default)
        self["scsi0:0.fileName"] = self.prefix + ".vmdk"
        self.connect_network()

    def read(self):
        for l in open(self.vmx_pathname):
            name, value = l.strip().split("=", 1)
            self[name] = value

    def write(self):
        f = open(self.vmx_pathname, "w")
        for name, value in sorted(self.items()):
            print >> f, '{0} = "{1}"'.format(name, value)

    def connect_iso(self, filename, device="ide0:0", present="TRUE"):
        self[device + ".deviceType"] = "cdrom-image"
        self[device + ".present"] = present
        self[device + ".fileName"] = filename
        self.write()

    def generate_mac(self):
        # we should check the mac isn't used as well
        seg1 = random.randint(0, 0x3f)
        seg2 = random.randint(0, 0xff)
        seg3 = random.randint(0, 0xff)
        return "00:50:56:{0:x}:{1:x}:{2:x}".format(seg1, seg2, seg3)

    def connect_network(self, interface="ethernet0", net_type="nat"):
        # http://sanbarrow.com/vmx/vmx-network-advanced.html

        # determines if the interface is used at all
        self[interface + ".present"] = "TRUE"

        # bridged, nat, hostonly, custom, monitor_dev
        self[interface + ".connectionType"] = net_type

        # e1000 always probably
        self[interface + ".virtualDev"] = "e1000"


        self[interface + ".startConnected"] = "TRUE"

        # static, generated or vpx
        self[interface + ".addressType"] ="static"

        # valid range is 00:50:56:00:00:00 to
        #                00:50:56:3f:ff:ff
        self[interface + ".address"] = self.generate_mac()

        self.write()

    default = {
            "displayname": "yaybu image",
            "annotation": "Created by Yaybu.",
            "guestos": "fedora",
            "config.version": "8",
            "virtualhw.version": "7",
            ".encoding": "UTF-8",

            "memsize": "256",
            "cpuid.coresPerSocket": "1",
            "numvcpus": "1",

            "scsi0.virtualDev": "lsilogic",
            "scsi0.present": "TRUE",
            "scsi0:0.present": "TRUE",
            "scsi0:0.fileName": "disk1.vmdk",
            "scsi0:0.mode": "persistent",
            "scsi0:0.deviceType": "disk",

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

class VMWare:

    def __init__(self, directory, prefix="yaybu"):
        self.directory = directory
        self.prefix = prefix
        # the abstraction. it leaks.
        self.uuid = os.path.basename(self.directory)
        self.vmx = VMX(directory, prefix)

    @property
    def id(self):
        """ Return a persistent unique identifier for the virtual machine,
        which is used by the compute node to manipulate it. Value is
        dependent on the underlying VM system. """
        return self.vmx.vmx_pathname

    @classmethod
    def create_node(klass, directory, base_image, prefix="yaybu", **settings):
        """ Create a new VMWare virtual machine in the specified directory from the base image. """
        os.mkdir(directory)
        pathname = os.path.join(directory, prefix + ".vmdk")
        qemu_img(base_image, pathname, "vmdk")
        vmware = klass(directory, prefix)
        vmware.connect_seed()
        vmware.vmx.update(settings)
        return vmware

    def connect_seed(self, seed_name="seed.iso"):
        seed_path = os.path.join(self.directory, seed_name)
        seed = cloudinit.Seed(seed_path, self.uuid)
        seed.update()
        self.vmx.connect_iso(seed_name)
        self.vmx.connect_iso("/usr/lib/vmware/isoimages/linux.iso", "ide0:1", "TRUE")
