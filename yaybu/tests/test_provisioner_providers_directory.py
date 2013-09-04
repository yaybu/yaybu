# coding=utf-8

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

import os
import pwd
import grp
import stat
from yaybu.tests.provisioner_fixture import TestCase


def sibpath(filename):
    return os.path.join(os.path.dirname(__file__), filename)


class TestDirectory(TestCase):

    def test_create_directory(self):
        self.chroot.check_apply("""
            resources:
              - Directory:
                  name: /etc/somedir
                  owner: root
                  group: root
            """)
        self.failUnless(self.chroot.isdir("/etc/somedir"))

    def test_create_directory_and_parents(self):
        self.chroot.check_apply("""
            resources:
                - Directory:
                    name: /etc/foo/bar/baz
                    parents: True
            """)
        self.failUnless(self.chroot.isdir("/etc/foo/bar/baz"))

    def test_remove_directory(self):
        self.chroot.mkdir("/etc/somedir")
        self.chroot.check_apply("""
            resources:
              - Directory:
                  name: /etc/somedir
                  policy: remove
        """)

    def test_remove_directory_recursive(self):
        self.chroot.mkdir("/etc/somedir")
        self.chroot.touch("/etc/somedir/child")
        self.chroot.check_apply("""
            resources:
                - Directory:
                    name: /etc/somedir
                    policy: remove-recursive
            """)
        self.failIfExists("/etc/somedir")

    def test_unicode(self):
        utf8 = "/etc/£££££" # this is utf-8 encoded
        self.chroot.check_apply(open(sibpath("assets/directory_unicode1.yay")).read())
        self.failUnlessExists(utf8)

    def test_attributes(self):
        self.chroot.check_apply("""
            resources:
              - Directory:
                  name: /etc/somedir2
                  owner: nobody
                  group: nogroup
                  mode: 0777
            """)
        self.failUnlessExists("/etc/somedir2")
        st = self.chroot.stat("/etc/somedir2")
        self.failUnless(pwd.getpwuid(st.st_uid)[0] != 'nobody')
        self.failUnless(grp.getgrgid(st.st_gid)[0] != 'nogroup')
        mode = stat.S_IMODE(st.st_mode)
        self.assertEqual(mode, 0777)

