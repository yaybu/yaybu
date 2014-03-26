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
                        "--port", "0", "--device", "0",
                        "--type", "dvddrive",
                        "--medium", "{filename}")

configure = vboxmanage("modifyvm", "{name}",
                       "--ioapic", "on",
                       "--boot1", "disk", "--boot2", "none",
                       "--memory", "{memsize}", "--vram", "128",
                       "--nic1", "bridged", "--bridgeadapter1", "e1000g0")


class VBoxMachineInstance(base.MachineInstance):

    name = "vbox"

    def __init__(self, directory, instance_id, **kwargs):
        self.instance_id = instance_id
        self.instance_dir = os.path.join(directory, instance_id)

    def check_state(self, state):
        """ Check the settings of the VM against the state, and do what is
        necessary to resolve any differences if possible. """

    @property
    def id(self):
        """ Return a persistent unique identifier for the virtual machine,
        which is used by the compute node to manipulate it. Value is
        dependent on the underlying VM system. """
        return self.instance_id


class VBoxCloudConfig(cloudinit.CloudConfig):

    def __init__(self, auth, **kwargs):
        cloudinit.CloudConfig.__init__(self, auth)


class VBoxUbuntuCloudConfig(VBoxCloudConfig):
    pass


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
    }

    def store_state(self):
        """ Write out the pertinent state details to the local state file, so we can manage change """
        if self.distro is not None:
            self.state.update(distro=self.distro)
        if self.release is not None:
            self.state.update(release=self.release)
        if self.seed is not None:
            if self.seed.password is not None:
                self.state.update(username=self.seed.username, password=self.seed.hashed_password)

    def create_disk(self, base_image):
        disk = os.path.join(self.instance_dir, self.instance.name + ".vdi")
        qemu_img(source=base_image, destination=disk, format="vdi")
        return disk

    def write(self, base_image, **kwargs):
        """ Create a new VMWare virtual machine in the specified directory from the base image. """

        distro = kwargs.pop("distro", None)
        #release = kwargs.pop("release", None)
        #arch = kwargs.pop("arch", None)
        auth = kwargs.pop("auth", None)
        #size = kwargs.pop("size", None)
        #cpus = kwargs.pop("cpus", None)
        #cores = kwargs.pop("cores", None)
        #ram = kwargs.pop("ram", None)

        # create the directory to hold all the bits
        os.mkdir(self.instance_dir)

        createvm(name=self.instance_id, directory=self.directory, ostype=self.ostype[distro])

        # create the disk image and attach it
        disk = self.create_disk(base_image)
        create_sata(name=self.instance_id)
        attach_disk(name=self.instance_id, disk=disk)

        # create the seed ISO
        config_class = self.configs[distro]
        cloud_config = config_class(auth, **kwargs)
        meta_data = cloudinit.MetaData(self.instance_id)
        seed = cloudinit.Seed(self.instance_dir, cloud_config=cloud_config,
                              meta_data=meta_data)
        seed.write()

        # connect the seed ISO and the tools ISO
        create_ide(name=self.instance_id)
        attach_ide(name=self.instance_id, filename=seed.pathname)
