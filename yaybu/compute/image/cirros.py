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

from . import base
import hashlib


class CirrosCloudImage(base.StandardCloudImage):

    server = "launchpad.net"
    source = "https://{server}/cirros/trunk/{release}/+download"
    prefix = "cirros-{release}-{arch}"
    image_suffix = "-disk.img"
    checksums = prefix + image_suffix + "/+md5"
    hash_function = hashlib.md5

    def image_hash(self, hashes):
        template = self.prefix + self.image_suffix
        filename = template.format(release=self.release, arch=self.arch)
        return hashes.get(filename, None)
