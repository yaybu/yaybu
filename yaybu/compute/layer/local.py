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

import os

from .base import Layer, AuthenticationError
from yaybu.core.util import memoized

from ..image.library import ImageLibrary


class Auth(object):
    pass


class PasswordAuth(Auth):
    def __init__(self, username, password):
        self.username = username
        self.password = password


class SSHAuth(Auth):
    def __init__(self, username, private_key, public_key):
        self.username = username
        self.private_key = private_key
        self.public_key = public_key


class Image(object):
    pass


class RemoteImage(Image):
    def __init__(self, url):
        self.url = url


class StandardImage(Image):
    def __init__(self, distro, release, arch):
        self.distro = distro
        self.release = release
        self.arch = arch


class Hardware(object):
    def __init__(self, memory, cpus):
        self.memory = memory
        self.cpus = cpus


class LocalComputeLayer(Layer):
    def __init__(self, original, yaybu_root="~/.yaybu"):
        super(LocalComputeLayer, self).__init__(original)
        self.machines = ImageLibrary(root=yaybu_root)

    @memoized
    @property
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

    @memoized
    @property
    def image(self):
        """ Image can look like one of these formats:

            image: http://server/path/image.img

            image:
              distro: ubuntu
              arch: amd64
              release: 12.04

        """
        p = self.original.params
        image = p.image.as_string(default=None)
        if image is not None:
            return RemoteImage(image)
        distro = p.image.distro.as_string(default=None)
        release = p.image.release.as_string(default=None)
        arch = p.image.arch.as_string(default=None)
        return StandardImage(distro, release, arch)

    @memoized
    @property
    def hardware(self):
        """ Standard hardware configuration. Currently supports:

        memory: 1024
        cpus: 2
        """
        memory = self.original.params.memory.as_string(default=None)
        cpus = self.original.params.cpus.as_string(default=None)
        return Hardware(memory, cpus)

    def price(self):
        """ Local implementations are free. \o/. """
        return None
