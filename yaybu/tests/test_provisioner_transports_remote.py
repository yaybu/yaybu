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
from yaybu.provisioner.transports.remote import RemoteTransport


class TestRemoteTransport(TestCase):

    def setUp(self):
        self.transport = RemoteTransport()
        self.ex = self.transport._execute = mock.Mock()

    def test_exists(self):
        self.ex.return_value = [0, "", ""]
        self.assertEqual(self.transport.exists("/"), True)
        self.ex.assert_called_with(["test", "-e", "/"])

    def test_not_exists(self):
        self.ex.return_value = [1, "", ""]
        self.assertEqual(self.transport.exists("/"), False)
        self.ex.assert_called_with(["test", "-e", "/"])

    def test_isdir(self):
        self.ex.return_value = [0, "", ""]
        self.assertEqual(self.transport.isdir("/"), True)
        self.ex.assert_called_with(["test", "-d", "/"])

    def test_not_isdir(self):
        self.ex.return_value = [1, "", ""]
        self.assertEqual(self.transport.isdir("/"), False)
        self.ex.assert_called_with(["test", "-d", "/"])

    def test_isfile(self):
        self.ex.return_value = [0, "", ""]
        self.assertEqual(self.transport.isfile("/"), True)
        self.ex.assert_called_with(["test", "-f", "/"])

    def test_not_isfile(self):
        self.ex.return_value = [1, "", ""]
        self.assertEqual(self.transport.isfile("/"), False)
        self.ex.assert_called_with(["test", "-f", "/"])

    def test_islink(self):
        self.ex.return_value = [0, "", ""]
        self.assertEqual(self.transport.islink("/"), True)
        self.ex.assert_called_with(["test", "-L", "/"])

    def test_not_islink(self):
        self.ex.return_value = [1, "", ""]
        self.assertEqual(self.transport.islink("/"), False)
        self.ex.assert_called_with(["test", "-L", "/"])

    def test_stat(self):
        self.ex.return_value = [
            0, "/ 4096 8 41ed 0 0 900 2 24 0 0 1379142318 1373968419 1373968419 0 4096", ""]
        self.transport.stat("/")
        self.ex.assert_called_with(["stat", "-L", "-t", "/"])
        # self.assertEqual(s.st_mode, 0755)

    def test_stat_not_exists(self):
        self.ex.return_value = [1, "", ""]
        self.assertRaises(OSError, self.transport.stat, "/")
        self.ex.assert_called_with(["stat", "-L", "-t", "/"])

    def test_lstat(self):
        self.ex.return_value = [
            0, "/ 4096 8 41ed 0 0 900 2 24 0 0 1379142318 1373968419 1373968419 0 4096", ""]
        self.transport.lstat("/")
        self.ex.assert_called_with(["stat", "-t", "/"])
        # self.assertEqual(s.st_mode, 0755)

    def test_lstat_not_exists(self):
        self.ex.return_value = [1, "", ""]
        self.assertRaises(OSError, self.transport.lstat, "/")
        self.ex.assert_called_with(["stat", "-t", "/"])

    def test_lexists(self):
        self.ex.return_value = [0, "", ""]
        self.assertEqual(self.transport.lexists("/"), True)
        self.ex.assert_called_with(["stat", "/"])

    def test_not_lexists(self):
        self.ex.return_value = [1, "", ""]
        self.assertEqual(self.transport.lexists("/"), False)
        self.ex.assert_called_with(["stat", "/"])

    def test_readlink(self):
        self.ex.return_value = [0, "/foo", ""]
        self.assertEqual(self.transport.readlink("/bar"), "/foo")
        self.ex.assert_called_with(["readlink", "/bar"])

    def test_readlink_doesnt_exist(self):
        self.ex.return_value = [1, "", ""]
        self.assertRaises(OSError, self.transport.readlink, "/bar")
        self.ex.assert_called_with(["readlink", "/bar"])

    def test_get(self):
        self.ex.return_value = [0, "hello\nhello\nhello\nhello\n", ""]
        self.assertEqual(
            self.transport.get("/proc/self/hello"), "hello\nhello\nhello\nhello\n")
        self.ex.assert_called_with(["cat", "/proc/self/hello"])

    def test_put(self):
        self.ex.return_value = [0, "", ""]
        self.transport.put("/foo", "hello\nworld")
        self.ex.assert_called_with(
            "umask 133 && tee /foo > /dev/null", stdin="hello\nworld")

    def test_makedirs(self):
        self.ex.return_value = [0, "", ""]
        self.transport.makedirs("/foo")
        self.ex.assert_called_with(["mkdir", "-p", "/foo"])

    def test_unlink(self):
        self.ex.return_value = [0, "", ""]
        self.transport.unlink("/foo")
        self.ex.assert_called_with(["rm", "-f", "/foo"])

    def test_getgrall(self):
        self.ex.return_value = [0, "mysql:x:144:", ""]
        groups = self.transport.getgrall()
        self.assertEqual(groups[0].gr_name, "mysql")

    def test_getgrnam(self):
        self.ex.return_value = [0, "mysql:x:144:", ""]
        group = self.transport.getgrnam("mysql")
        self.assertEqual(group.gr_name, "mysql")

    def test_getgrnam_miss(self):
        self.ex.return_value = [0, "mysql:x:144:", ""]
        self.assertRaises(KeyError, self.transport.getgrnam, "sqlite")

    def test_getgrgid(self):
        self.ex.return_value = [0, "mysql:x:144:", ""]
        group = self.transport.getgrgid(144)
        self.assertEqual(group.gr_name, "mysql")

    def test_getgrgid_miss(self):
        self.ex.return_value = [0, "mysql:x:144:", ""]
        self.assertRaises(KeyError, self.transport.getgrgid, 129)

    def test_getpwall(self):
        self.ex.return_value = [
            0, "mysql:x:129:144:MySQL Server,,,:/nonexistent:/bin/false", ""]
        users = self.transport.getpwall()
        self.assertEqual(users[0].pw_name, "mysql")

    def test_getpwnam(self):
        self.ex.return_value = [
            0, "mysql:x:129:144:MySQL Server,,,:/nonexistent:/bin/false", ""]
        user = self.transport.getpwnam("mysql")
        self.assertEqual(user.pw_name, "mysql")

    def test_getpwnam_miss(self):
        self.ex.return_value = [
            0, "mysql:x:129:144:MySQL Server,,,:/nonexistent:/bin/false", ""]
        self.assertRaises(KeyError, self.transport.getpwnam, "sqlite")

    def test_getpwuid(self):
        self.ex.return_value = [
            0, "mysql:x:129:144:MySQL Server,,,:/nonexistent:/bin/false", ""]
        user = self.transport.getpwuid(129)
        self.assertEqual(user.pw_name, "mysql")

    def test_getpwuid_miss(self):
        self.ex.return_value = [
            0, "mysql:x:129:144:MySQL Server,,,:/nonexistent:/bin/false", ""]
        self.assertRaises(KeyError, self.transport.getpwuid, 144)

    def test_getspall(self):
        self.ex.return_value = [0, "mysql:!:15958:0:99999:7:::", ""]
        shadows = self.transport.getspall()
        self.assertEqual(shadows[0].sp_nam, "mysql")

    def test_getspnam(self):
        self.ex.return_value = [0, "mysql:!:15958:0:99999:7:::", ""]
        shadow = self.transport.getspnam("mysql")
        self.assertEqual(shadow.sp_nam, "mysql")

    def test_getspnam_miss(self):
        self.ex.return_value = [0, "mysql:!:15958:0:99999:7:::", ""]
        self.assertRaises(KeyError, self.transport.getspnam, "sqlite")
