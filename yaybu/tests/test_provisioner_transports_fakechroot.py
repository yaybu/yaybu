# Copyright 2013 Isotoma Limited
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

import mock

from yaybu.tests.provisioner_fixture import TestCase
from yaybu.provisioner.transports.fakechroot import FakechrootTransport


class AFakechrootTransport(FakechrootTransport):

    def communicate(self, *args):
        return 0, "hello", "goodbye"


class TestBaseTransport(TestCase):

    def setUp(self):
        self.transport = AFakechrootTransport(None, 9, True)

    def test_connect(self):
        self.transport.connect()

    def test_whoami(self):
        # Fakechroot 'connection' is always as root
        self.assertEqual(self.transport.whoami(), "root")

    @mock.patch("yaybu.provisioner.transports.local.subprocess")
    def test_execute(self, subprocess):
        self.transport.overlay_dir = "/bin"
        self.transport.env = {"FAKECHROOT_BASE": "/tmp", "PATH": "/hello"}
        self.assertEqual(self.transport.execute(
            ["/usr/bin/whoami"]), (0, "hello", "goodbye"))
