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

from yaybu.tests.provisioner_fixture import TestCase
from yaybu import error


class TestGroup(TestCase):

    def test_simple_group(self):
        self.chroot.check_apply("""
            resources:
                - Group:
                    name: test
            """)

        self.failUnless(self.chroot.get_group("test"))

    def test_group_with_gid(self):
        self.chroot.check_apply("""
            resources:
                - Group:
                    name: test
                    gid: 1111
            """)

        self.failUnless(self.chroot.get_group("test"))

    def test_existing_group(self):
        """ Test creating a group whose name already exists. """

        self.failUnless(self.chroot.get_group("users"))

        self.assertRaises(error.NothingChanged, self.chroot.apply, """
            resources:
                - Group:
                    name: users
            """)

        self.failUnless(self.chroot.get_group("users"))

    def test_existing_gid(self):
        """ Test creating a group whose specified gid already exists. """
        self.assertRaises(error.InvalidGroup, self.chroot.apply, """
            resources:
                - Group:
                    name: test
                    gid: 100
            """)
        self.failUnlessRaises(KeyError, self.chroot.get_group, "test")

    def test_add_group_and_use_it(self):
        self.chroot.check_apply("""
            resources:
                - Group:
                    name: test
                - File:
                    name: /etc/test
                    group: test
                - Execute:
                    name: test-group
                    command: python -c "import os, grp; open('/etc/test2', 'w').write(grp.getgrgid(os.getgid()).gr_name)"
                    creates: /etc/test2
                    group: test
            """)
        self.failUnlessEqual(self.chroot.open("/etc/test2").read(), "test")


class TestGroupRemove(TestCase):

    def test_remove_existing(self):
        self.failUnless(self.chroot.get_group("users"))

        self.chroot.check_apply("""
            resources:
                - Group:
                    name: users
                    policy: remove
            """)

        self.failUnlessRaises(KeyError, self.chroot.get_group, "users")

    def test_remove_non_existing(self):
        self.failUnlessRaises(KeyError, self.chroot.get_group, "zzidontexistzz")

        self.assertRaises(error.NothingChanged, self.chroot.apply, """
            resources:
                - Group:
                    name: zzidontexistzz
                    policy: remove
            """)

        self.failUnlessRaises(KeyError, self.chroot.get_group, "zzidontexistzz")


