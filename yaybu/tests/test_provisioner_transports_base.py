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
from yaybu.provisioner.transports.base import Transport


class ATestTransport(Transport):

    def whoami(self):
        return "root"


class TestBaseTransport(TestCase):

    def setUp(self):
        self.transport = ATestTransport(None, 9, True)
        self.transport._execute_impl = mock.Mock()

    def test_simple(self):
        self.transport.execute(["foo"])
        self.transport._execute_impl.assert_called_with(
            ['env', '-i', 'PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin',
                'SHELL=/bin/sh', 'LOGNAME=root', 'sh', '-c', 'cd /; foo'],
            None, None, None,
        )

    def test_change_user(self):
        self.transport.execute(["foo"], user="doug")
        self.transport._execute_impl.assert_called_with(
            ['sudo', '-u', 'doug', '--', 'env', '-i', 'PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin',
                'SHELL=/bin/sh', 'LOGNAME=doug', 'sh', '-c', 'cd /; foo'],
            None, None, None
        )

    def test_change_group(self):
        self.transport.execute(["foo"], group="staff")
        self.transport._execute_impl.assert_called_with(
            ['sudo', '-g', 'staff', '--', 'env', '-i', 'PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin',
                'SHELL=/bin/sh', 'LOGNAME=root', 'sh', '-c', 'cd /; foo'],
            None, None, None
        )

    def test_change_user_and_group(self):
        self.transport.execute(["foo"], user="doug", group="staff")
        self.transport._execute_impl.assert_called_with(
            ['sudo', '-u', 'doug', '-g', 'staff', '--', 'env', '-i', 'PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin',
                'SHELL=/bin/sh', 'LOGNAME=doug', 'sh', '-c', 'cd /; foo'],
            None, None, None
        )
