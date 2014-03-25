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
import uuid
import urllib2

from . import ubuntu
from . import fedora
from . import cirros
from . import error
from . import vmware
from . import cloudinit

class ImageLibrary:

    """ A library of virtual machines, and a mechanism for adding packaged
    virtual machines to the library from local or remote locations.

    The directory structure resembles:

    ~/.yaybu/
        /instances/
            /vmware/
                <UUID>/
            /vbox/
                <UUID/
        /images/
            /<distro>/
                <release>-<arch>.qcow2
                <release>-<arch>.vmdk
        /temp/
    """

    distributions = {
        "ubuntu": ubuntu.UbuntuCloudImage,
        "fedora": fedora.FedoraCloudImage,
        "cirros": cirros.CirrosCloudImage,
    }

    systems = {
        "vmware": vmware.VMWare,
    }

    def __init__(self, root="~/.yaybu"):
        self.root = os.path.expanduser(root)
        self.imagedir = os.path.join(self.root, "library")
        self.instancedir = os.path.join(self.root, "instances")
        self.tempdir = os.path.join(self.root, "temp")
        self.setupdirs()

    def setupdirs(self):
        """ Create directories if required """
        imagedirs = [os.path.join(self.imagedir, x) for x in self.distributions.keys() + ["user"]]
        systemdirs = [os.path.join(self.instancedir, x) for x in self.systems.keys()]
        for d in [self.imagedir, self.instancedir, self.tempdir] + imagedirs + systemdirs:
            if not os.path.exists(d):
                os.makedirs(d)

    def get_canonical(self, distro, release, arch, context=None):
        """ Fetches the specified uri into the cache and then extracts it
        into the library.  If name is None then a name is made up.

        Arguments:
            distro: the name of the distribution, i.e. Ubuntu, Fedora
            release: the distribution's name for the release, i.e. 12.04
            arch: the distribution's name for the architecture, i.e. x86_64, amd64
            format: the format of virtual machine image required, i.e. vmdk, qcow
        """
        klass = self.distributions.get(distro, None)
        if klass is None:
            raise error.DistributionNotKnown()
        with context.ui.throbber("Fetching distro image"):
            pathname = os.path.join(self.imagedir, distro, "{0}-{1}.qcow2".format(release, arch))
            distro = klass(pathname, release, arch)
            distro.update()
        return pathname

    def get_remote(self, remote_url, context=None):
        urihash = hashlib.sha256()
        urihash.update(remote_url)
        pathname = os.path.join(self.imagedir, "user", "{0}.qcow2".format(urihash.hexdigest()))
        with context.ui.throbber("Retrieving {0} to {1}".format(remote_url, pathname)):
            try:
                response = urllib2.urlopen(remote_url)
            except urllib2.HTTPError:
                raise error.FetchFailedException("Unable to fetch {0}".format(remote_url))
            local = open(pathname, "w")
            while True:
                data = response.read(81920)
                if not data:
                    break
                local.write(data)
        return pathname

    def get_system_driver(self, name):
        klass = self.systems.get(name, None)
        if klass is None:
            raise error.SystemNotKnown()
        return klass

    def instances(self, system):
        """ Return a generator of instance objects. """
        driver = self.get_system_driver(system)
        systemdir = os.path.join(self.instancedir, system)
        for d in os.listdir(systemdir):
            pathname = os.path.join(systemdir, d)
            yield driver(pathname)

    def create_seed(self, directory, instance_id):
        meta_data = cloudinit.MetaData(instance_id)
        user_data = cloudinit.CloudConfig()
        fpath = os.path.join(directory, "seed.iso")
        seed = cloudinit.Seed(fpath, [meta_data, user_data])
        seed.create()
        return fpath

    def create_node(self, system, base_image, auth, name, size, **kwargs):
        """ Create an instance from the provided base image """
        klass = self.get_system_driver(system)
        instance_id = str(uuid.uuid4())
        instancedir = os.path.join(self.instancedir, system, instance_id)
        os.mkdir(instancedir)
        filename = self.create_seed(instancedir, instance_id)
        vm = klass.create_node(instancedir, base_image, auth=auth, name=name, size=size, **kwargs)
        vm.connect_seed(filename)
        vm.connect_tools()
        return vm
