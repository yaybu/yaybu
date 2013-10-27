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
from yaybu.provisioner.transports.local import LocalTransport
from yaybu.provisioner.transports.remote import stat_result


class TestLocalTransport(TestCase):

    def setUp(self):
        for modname in ("os", "pwd", "grp", "spwd"):
            patcher = mock.patch(
                "yaybu.provisioner.transports.local.%s" % modname)
            self.addCleanup(patcher.stop)
            setattr(self, modname, patcher.start())

        self.transport = LocalTransport(None)

    def test_whoami(self):
        self.pwd.getpwuid.return_value.pw_name = "root"
        self.assertEqual(self.transport.whoami(), "root")
        self.os.getuid.assert_called_with()

    def test_exists(self):
        self.os.path.exists.return_value = True
        self.assertEqual(self.transport.exists("/"), True)
        self.os.path.exists.assert_called_with("/")

    def test_not_exists(self):
        self.os.path.exists.return_value = False
        self.assertEqual(self.transport.exists("/"), False)
        self.os.path.exists.assert_called_with("/")

    def test_isfile(self):
        self.os.path.isfile.return_value = True
        self.assertEqual(self.transport.isfile("/"), True)
        self.os.path.isfile.assert_called_with("/")

    def test_not_isfile(self):
        self.os.path.isfile.return_value = False
        self.assertEqual(self.transport.isfile("/"), False)
        self.os.path.isfile.assert_called_with("/")

    def test_isdir(self):
        self.os.path.isdir.return_value = True
        self.assertEqual(self.transport.isdir("/"), True)
        self.os.path.isdir.assert_called_with("/")

    def test_not_isdir(self):
        self.os.path.isdir.return_value = False
        self.assertEqual(self.transport.isdir("/"), False)
        self.os.path.isdir.assert_called_with("/")

    def test_islink(self):
        self.os.path.islink.return_value = True
        self.assertEqual(self.transport.islink("/"), True)
        self.os.path.islink.assert_called_with("/")

    def test_not_islink(self):
        self.os.path.islink.return_value = False
        self.assertEqual(self.transport.islink("/"), False)
        self.os.path.islink.assert_called_with("/")

    def test_stat(self):
        self.os.stat.return_value = stat_result(
            0o755, 0, 0, 0, 0, 0, 0, 0, 0, 0)
        self.assertEqual(self.transport.stat("/").st_mode, 0o755)
        self.os.stat.assert_called_with("/")

    def test_stat_not_exists(self):
        self.os.stat.side_effect = OSError
        self.assertRaises(OSError, self.transport.stat, "/")
        self.os.stat.assert_called_with("/")

    def test_lstat(self):
        self.os.lstat.return_value = stat_result(
            0o755, 0, 0, 0, 0, 0, 0, 0, 0, 0)
        self.assertEqual(self.transport.lstat("/").st_mode, 0o755)
        self.os.lstat.assert_called_with("/")

    def test_lstat_not_exists(self):
        self.os.lstat.side_effect = OSError
        self.assertRaises(OSError, self.transport.lstat, "/")
        self.os.lstat.assert_called_with("/")

    def test_lexists(self):
        self.os.path.lexists.return_value = True
        self.assertEqual(self.transport.lexists("/"), True)
        self.os.path.lexists.assert_called_with("/")

    def test_not_lexists(self):
        self.os.path.lexists.return_value = False
        self.assertEqual(self.transport.lexists("/"), False)
        self.os.path.lexists.assert_called_with("/")

    def test_readlink(self):
        self.os.readlink.return_value = "/"
        self.assertEqual(self.transport.readlink("/bar"), "/")
        self.os.readlink.assert_called_with("/bar")

    def test_notexists_readlink(self):
        self.os.readlink.side_effect = OSError
        self.assertRaises(OSError, self.transport.readlink, "/bar")
        self.os.readlink.assert_called_with("/bar")

    # def test_get(self):
    #    self.ex.return_value = [0, "hello\nhello\nhello\nhello\n", ""]
    #    self.assertEqual(self.transport.get("/proc/self/hello"), "hello\nhello\nhello\nhello\n")
    #    self.ex.assert_called_with(["cat", "/proc/self/hello"])

    # def test_put(self):
    #    self.ex.return_value = [0, "", ""]
    #    self.transport.put("/foo", "hello\nworld")
    #    self.ex.assert_called_with("umask 133 && tee /foo > /dev/null", stdin="hello\nworld")

    def test_makedirs(self):
        self.os.makedirs.return_value = None
        self.transport.makedirs("/foo")
        self.os.makedirs.assert_called_with("/foo")

    def test_unlink(self):
        self.os.unlink.return_value = None
        self.transport.unlink("/foo")
        self.os.unlink.assert_called_with("/foo")

    def test_getgrall(self):
        self.grp.getgrall.return_value = ["mysql"]
        groups = self.transport.getgrall()
        self.assertEqual(groups[0], "mysql")

    def test_getgrnam(self):
        self.grp.getgrnam.return_value = "mysql"
        group = self.transport.getgrnam("mysql")
        self.assertEqual(group, "mysql")

    def test_getgrnam_miss(self):
        self.grp.getgrnam.side_effect = KeyError
        self.assertRaises(KeyError, self.transport.getgrnam, "sqlite")

    def test_getgrgid(self):
        self.grp.getgrgid.return_value = "mysql"
        group = self.transport.getgrgid(0)
        self.assertEqual(group, "mysql")

    def test_getgrgid_miss(self):
        self.grp.getgrgid.side_effect = KeyError
        self.assertRaises(KeyError, self.transport.getgrgid, "sqlite")

    def test_getpwall(self):
        self.pwd.getpwall.return_value = ["mysql"]
        groups = self.transport.getpwall()
        self.assertEqual(groups[0], "mysql")

    def test_getpwnam(self):
        self.pwd.getpwnam.return_value = "mysql"
        group = self.transport.getpwnam("mysql")
        self.assertEqual(group, "mysql")

    def test_getpwnam_miss(self):
        self.pwd.getpwnam.side_effect = KeyError
        self.assertRaises(KeyError, self.transport.getpwnam, "sqlite")

    def test_getpwuid(self):
        self.pwd.getpwuid.return_value = "mysql"
        group = self.transport.getpwuid(0)
        self.assertEqual(group, "mysql")

    def test_getpwuid_miss(self):
        self.pwd.getpwuid.side_effect = KeyError
        self.assertRaises(KeyError, self.transport.getpwuid, "sqlite")

    def test_getspall(self):
        self.spwd.getspall.return_value = ["password"]
        shadows = self.transport.getspall()
        self.assertEqual(shadows[0], "password")

    def test_getspnam(self):
        self.spwd.getspnam.return_value = "password"
        shadow = self.transport.getspnam("mysql")
        self.assertEqual(shadow, "password")

    def test_getspnam_miss(self):
        self.spwd.getspnam.side_effect = KeyError
        self.assertRaises(KeyError, self.transport.getspnam, "sqlite")
