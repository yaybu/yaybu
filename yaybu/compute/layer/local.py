# Copyright 2012 Isotoma Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import time
import os
import abc

from .base import Layer, AuthenticationError
from yaybu.core.util import memoized
from yay import errors

from yaybu.compute.image import PasswordAuth, SSHAuth, RemoteImage, CanonicalImage, ImageLibrary, Hardware, MachineSpec


class NodeState:
    EMPTY = 1
    STARTING = 2
    RUNNING = 3


class LocalComputeLayer(Layer):

    """ Adapts the compute part. Parses the provided configuration to determine how to start the specified node. """

    __metaclass__ = abc.ABCMeta

    wait_delay = 30

    def __init__(self, original, yaybu_root="~/.yaybu"):
        super(LocalComputeLayer, self).__init__(original)
        self.machines = ImageLibrary(root=yaybu_root)
        self.node = None

    def start(self):
        """ Start self.node """
        if self.node is None:
            raise ValueError("Trying to start a node that does not exist")
        self.node.start()

    def destroy(self):
        if self.node is None:
            raise ValueError("Trying to destroy a node that does not exist")
        self.node.destroy()
        self.node = None

    @abc.abstractmethod
    def options(self):
        """ Return additional options to be passed to the builder """

    def create(self):
        if self.node is not None:
            raise ValueError("Trying to create a node when we already have one")
        builder = self.machines.get_builder(self.system)
        self.node = builder.create(self.spec)
        self.start()

    def load(self, name):
        if self.node is not None:
            raise ValueError("Trying to start a node when we already have one")
        for vm in self.machines.instances(self.system):
            if vm.name == name:
                self.node = vm
                self.start()
                return

    def wait(self):
        for i in range(self.wait_delay):
            if self.public_ip:
                self.state = NodeState.RUNNING
                return
            else:
                time.sleep(1)

    @property
    @memoized
    def name(self):
        return self.original.params.name.as_string()

    @property
    @memoized
    def spec(self):
        return MachineSpec(
            name=self.name,
            auth=self.auth,
            image=self.image,
            hardware=self.hardware,
            options=self.options,
        )

    @property
    @memoized
    def auth(self):
        """ Return an instance of Auth appropriate for the configuration.

        We use in preference, if provided:

         1. literal SSH keyfile names
         2. a password
         3. an ssh key in the user's .ssh directory

        If nothing is provided, we use ~/.ssh/id_rsa
        """
        p = self.original.params
        username = p.user.as_string(default="yaybu")
        password = p.password.as_string(default=None)
        key = p.key.as_string(default="id_rsa")
        public_key = p.public_key.as_string(default=None)
        private_key = p.private_key.as_string(default=None)

        if public_key is not None and private_key is not None:
            return SSHAuth(username, private_key, public_key)
        if public_key is not None or private_key is not None:
            raise AuthenticationError("One of public_key or private_key is specified, but not both")

        if password is not None:
            return PasswordAuth(username, password)

        private_key = os.path.expanduser(os.path.join("~/.ssh", key))
        if not os.path.exists(private_key):
            raise AuthenticationError("Private key file %r does not exist" % private_key)
        public_key = private_key + ".pub"
        if not os.path.exists(public_key):
            raise AuthenticationError("Public key file %r does not exist" % public_key)
        return SSHAuth(username, private_key, public_key)

    @property
    @memoized
    def image(self):
        """ Image can look like one of these formats:

            image: http://server/path/image.img

            image:
              distro: ubuntu
              arch: amd64
              release: 12.04

        """
        p = self.original.params
        try:
            url = p.image.as_string()
            image = RemoteImage(url)
        except errors.TypeError:
            distro = p.image.distro.as_string(default=None)
            release = p.image.release.as_string(default=None)
            arch = p.image.arch.as_string(default=None)
            image = CanonicalImage(distro, release, arch)
        return image

    @property
    @memoized
    def hardware(self):
        """ Standard hardware configuration. Currently supports:

        memory: 1024
        cpus: 2
        """
        memory = self.original.params.memory.as_string(default="256")
        cpus = self.original.params.cpus.as_string(default="1")
        return Hardware(memory, cpus)

    @property
    def price(self):
        """ Local implementations are free. \o/. """
        return None

    @property
    def domain(self):
        return "unknown-domain"

    @property
    def fqdn(self):
        return self.public_ip

    @property
    def hostname(self):
        return "unknown-hostname"

    @property
    def location(self):
        return self.public_ip

    @property
    def private_ip(self):
        return None

    @property
    def private_ips(self):
        return []

    @property
    def public_ips(self):
        return [self.public_ip]

    @property
    def public_ip(self):
        return self.node.get_ip()
