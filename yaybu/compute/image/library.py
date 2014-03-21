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

from . import cloudinit
from . import ubuntu
from . import fedora
from . import cirros


class ImageLibrary:

    """ A library of virtual machines, and a mechanism for adding packaged
    virtual machines to the library from local or remote locations.

    The directory structure resembles:

    ~/.yaybu/
        /instances/<UUID>/<vm files>
        /images/<filename>/
            <filename>.qcow2
            <filename>.vmdk
        /temp/<UUID>/<temp files>
    """

    distributions = {
        "ubuntu": ubuntu.UbuntuCloudImage,
        "fedora": fedora.FedoraCloudImage,
        "cirros": cirros.CirrosCloudImage,
    }

    def __init__(self, root="~/.yaybu"):
        self.root = os.path.expanduser(root)
        self.library = {}
        # a set of images that are only cloned
        self.librarydir = os.path.join(self.root, "library")
        # instances that may be started and running
        self.instancedir = os.path.join(self.root, "instances")
        # A temporary directory, we put it here so we know we have enough room
        self.tempdir = os.path.join(self.root, "temp")
        self.setupdirs()
        self.scan()

    def setupdirs(self):
        """ Create directories if required """
        for d in self.librarydir, self.instancedir, self.tempdir:
            if not os.path.exists(d):
                os.makedirs(d)

    def scan(self):
        """ Scan the library and populate self.library. self.library looks like:

        { "<image hash>": {
            "qcow2": "ubuntu-<release>-<arch>.qcow2",
            "vmdk": "ubuntu-<release>-<arch>.vmdk",
            },
        }
        """
        for item in os.listdir(self.librarydir):
            ip = os.path.join(self.librarydir, item)
            if os.path.isdir(ip):
                self.library[item] = {}
                for img in os.listdir(ip):
                    ext = img.rsplit(".", 1)
                    self.library[item][ext] = img

    #def guess_name(self, uri):
        #""" Use the name of the file with the extension stripped off """
        #path = urlparse.urlparse(uri).path
        #leaf = path.split("/")[-1]
        #if not leaf:
            #raise VMException("Cannot guess name for %r" % (uri,))
        #return leaf.rsplit(".", 1)[0]

    def uri_hash(self, uri):
        h = hashlib.sha256()
        h.update(uri)
        return h.hexdigest()

    def get(self, distro, release, arch, format, context=None):
        """ Fetches the specified uri into the cache and then extracts it
        into the library.  If name is None then a name is made up.

        Arguments:
            distro: the name of the distribution, i.e. Ubuntu, Fedora
            release: the distribution's name for the release, i.e. 12.04
            arch: the distribution's name for the architecture, i.e. x86_64, amd64
            format: the format of virtual machine image required, i.e. vmdk, qcow
        """

    def instances(self):
        """ Return a generator of VMWareVM objects. """


class CloudInit:

    def __init__(self, directory, image):
        self.directory = directory
        self.image = image

    def create_seed(self):
        """ Create a seed ISO image in the specified filename """
        s = cloudinit.Seed(os.path.join(self.directory, "seed.iso"))
        s.update()
        s.save()
        s.cleanup()

    def fetch_image(self):
        self.image.update()
        self.image.make_vmx()

#if __name__ == "__main__":
    #import sys
    #logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
    #directory = os.path.realpath("cloudinit")
    #if not os.path.exists(directory):
        #os.mkdir(directory)
    ##image = UbuntuCloudImage(directory, "13.10", "amd64")
    #image = fedora.FedoraCloudImage(directory, "20", "x86_64")
    #image = cirros.CirrosCloudImage(directory, "0.3.0", "x86_64")
    #cloudinit = library.CloudInit(directory, image)
    #cloudinit.create_seed()
    #cloudinit.fetch_image()
