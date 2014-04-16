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

import os
import logging
import shutil

from . import cloudinit
from . import base

from yaybu.compute.util import SubRunner

logger = logging.getLogger("vbox")

qemu_img = SubRunner(
    command_name="qemu-img",
    args=["convert", "-O", "{format}", "{source}", "{destination}"],
)


def vboxmanage(*args):
    return SubRunner(command_name="VBoxManage", args=args)

createvm = vboxmanage("createvm",
                      "--name", "{name}",
                      "--basefolder", "{directory}",
                      "--ostype", "{ostype}",
                      "--register")

create_sata = vboxmanage("storagectl", "{name}",
                         "--name", '"SATA Controller"',
                         "--add", "sata",
                         "--controller", "IntelAHCI")

create_ide = vboxmanage("storagectl", "{name}",
                        "--name", '"IDE Controller"',
                        "--add", "ide")

attach_disk = vboxmanage("storageattach", "{name}",
                         "--storagectl", '"SATA Controller"',
                         "--port", "0", "--device", "0",
                         "--type", "hdd",
                         "--medium", "{disk}")

attach_ide = vboxmanage("storageattach", "{name}",
                        "--storagectl", '"IDE Controller"',
                        "--port", "{port}", "--device", "{device}",
                        "--type", "dvddrive",
                        "--medium", "{filename}")

configurevm = vboxmanage("modifyvm", "{name}",
                       "--ioapic", "on",
                       "--boot1", "disk", "--boot2", "none",
                       "--memory", "{memsize}", "--vram", "12",
                       "--uart1", "0x3f8", "4",
                       "--uartmode1", "disconnected")

startvm = vboxmanage("startvm",
                     "--type", "{type}",
                     "{name}")

unregistervm = vboxmanage("unregistervm",
                          "{name}", "--delete")

guestproperty = vboxmanage("guestproperty", "get", "{name}", "{property}")


def test_connection():
    return startvm.pathname is not None


class VBoxMachineInstance(base.MachineInstance):

    name = "vbox"

    @property
    def id(self):
        return self.instance_id

    def _start(self):
        startvm(type="gui", name=self.instance_id)

    def _destroy(self):
        unregistervm(name=self.node)
        shutil.rmtree(os.path.dirname(self.node))

    def get_ip(self):
        s = guestproperty(name=self.instance_id, property="/VirtualBox/GuestInfo/Net/0/V4/IP")
        if s.startswith("Value: "):
            return s.split(" ", 1)[1]


class VBoxCloudConfig(cloudinit.CloudConfig):
    runcmd = [
        ['mount', '/dev/sr1', '/mnt'],
        ['/mnt/VBoxLinuxAdditions.run'],
        ['umount', '/mnt'],
    ]


class VBoxUbuntuCloudConfig(VBoxCloudConfig):
    #package_update = True
    #package_upgrade = True
    packages = ['build-essential']


class VBoxFedoraCloudConfig(VBoxCloudConfig):

    pass


class VBoxMachineBuilder(base.MachineBuilder):

    instance = VBoxMachineInstance

    configs = {
        "ubuntu": VBoxUbuntuCloudConfig,
        "fedora": VBoxFedoraCloudConfig,
    }

    ostype = {
        "ubuntu": "Ubuntu_64",
        "fedora": "Fedora_64",
        None: "Linux_64",
    }

    def create(self, spec):
        """ Create a new virtual machine in the specified directory from the base image. """

        assert isinstance(spec, base.MachineSpec)

        instance_id = self.get_instance_id(spec)
        instance_dir = os.path.join(self.directory, instance_id)
        # create the directory to hold all the bits
        os.mkdir(instance_dir)

        createvm(name=instance_id,
                 directory=self.directory,
                 ostype=self.ostype[spec.image.distro])
        configurevm(name=spec.name, memsize=spec.hardware.memory)

        # create the disk image and attach it
        disk = os.path.join(instance_dir, instance_id + "_disk1.vdi")
        qemu_img(source=spec.image.fetch(self.image_dir), destination=disk, format="vdi")
        create_sata(name=instance_id)
        attach_disk(name=instance_id, disk=disk)

        # create the seed ISO
        config_class = self.configs[spec.image.distro]
        cloud_config = config_class(spec.auth)
        meta_data = cloudinit.MetaData(spec.name)
        seed = cloudinit.Seed(instance_dir, cloud_config=cloud_config, meta_data=meta_data)
        seed.write()

        # connect the seed ISO and the tools ISO
        create_ide(name=instance_id)
        attach_ide(name=instance_id, port="0", device="0", filename=seed.pathname)
        attach_ide(name=instance_id, port="0", device="1", filename="/usr/share/virtualbox/VBoxGuestAdditions.iso")
        return VBoxMachineInstance(instance_dir, spec.name)
