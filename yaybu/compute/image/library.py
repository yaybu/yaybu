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
import hashlib
import urllib2
import datetime

from . import error
from . import vmware
from . import vbox

from base import RemoteImage, CanonicalImage, PasswordAuth, SSHAuth


class ImageLibrary:

    """ A library of virtual machines, and a mechanism for adding packaged
    virtual machines to the library from local or remote locations. """

    seed_iso_name = "seed.iso"

    systems = {
        "vmware": (vmware.VMWareMachineInstance, vmware.VMWareMachineBuilder),
        "vbox": (vbox.VBoxMachineInstance, vbox.VBoxMachineBuilder),
    }

    def __init__(self, root="~/.yaybu"):
        self.root = os.path.expanduser(root)
        self.imagedir = os.path.join(self.root, "library")
        self.instancedir = os.path.join(self.root, "instances")
        self.tempdir = os.path.join(self.root, "temp")
        self.setupdirs()

    def setupdirs(self):
        """ Create directories if required """
        systemdirs = [os.path.join(self.instancedir, x) for x in self.systems.keys()]
        for d in [self.imagedir, self.instancedir, self.tempdir] + systemdirs:
            if not os.path.exists(d):
                os.makedirs(d)

    def fetch(self, image):
        return image.fetch(self.imagedir)

    def get_system_driver(self, name):
        if name not in self.systems:
            raise error.SystemNotKnown()
        return self.systems[name]

    def instances(self, system):
        """ Return a generator of instance objects. """
        driver, _ = self.get_system_driver(system)
        systemdir = os.path.join(self.instancedir, system)
        for d in os.listdir(systemdir):
            yield driver(systemdir, d)

    def get_instance_id(self, directory, name):
        today = datetime.datetime.now()
        instance_id = "{0}-{1:%Y-%m-%d}".format(name, today)
        count = 1
        while True:
            pathname = os.path.join(directory, instance_id)
            if not os.path.exists(pathname):
                break
            instance_id = "{0}-{1:%Y-%m-%d}-{2:02}".format(name, today, count)
            count = count + 1
        return instance_id

    def create_node(self, name, system, distro, base_image, state, auth, hardware, **kwargs):
        """ Create an instance from the provided base image """
        instance, builder = self.get_system_driver(system)
        system_dir = os.path.join(self.instancedir, system)
        if name is None:
            name = system
        instance_id = self.get_instance_id(system_dir, name)
        print "Creating", instance_id
        b = builder(system_dir, state, instance_id)
        b.write(
            base_image=base_image,
            distro=distro,
            state=state,
            auth=auth,
            hardware=hardware,
            **kwargs)
        machine = instance(system_dir, instance_id)
        machine.apply_changes(state=state, auth=auth, hardware=hardware, **kwargs)
        return machine
