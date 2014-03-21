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

import hashlib

from . import base


class FedoraCloudImage(base.StandardCloudImage):

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
