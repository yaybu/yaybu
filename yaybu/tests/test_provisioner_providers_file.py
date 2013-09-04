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
from yaybu.core import error
import pwd
import grp
import os
import stat

def sibpath(filename):
    return os.path.join(os.path.dirname(__file__), filename)

class TestFileApply(TestCase):

    def test_create_missing_component(self):
        self.assertRaises(error.PathComponentMissing, self.chroot.apply, """
            resources:
              - File:
                  name: /etc/missing/filename
            """)

    def test_create_missing_component_simulate(self):
        """
        Right now we treat missing directories as a warning in simulate mode, as other outside processes might have created them.
        Later on we might not generate warnings for resources we can see will be created
        """
        self.chroot.apply("""
            resources:
              - File:
                  name: /etc/missing/filename
            """, "--simulate")

    def test_create_file(self):
        self.chroot.check_apply("""
            resources:
              - File:
                  name: /etc/somefile
                  owner: root
                  group: root
            """)

        self.failUnlessExists("/etc/somefile")

    def test_attributes(self):
        self.chroot.check_apply("""
            resources:
              - File:
                  name: /etc/somefile2
                  owner: nobody
                  group: nogroup
                  mode: 0666
            """)
        self.failUnlessExists("/etc/somefile2")
        st = self.chroot.stat("/etc/somefile2")
        self.failUnless(pwd.getpwuid(st.st_uid)[0] != 'nobody')
        self.failUnless(grp.getgrgid(st.st_gid)[0] != 'nogroup')
        mode = stat.S_IMODE(st.st_mode)
        self.assertEqual(mode, 0666)

    def test_create_file_template(self):
        self.chroot.check_apply("""
            resources:
                - File:
                    name: /etc/templated
                    template: {{ "package://yaybu.tests/assets/template1.j2" }}
                    template_args:
                        foo: this is foo
                        bar: 42
                    owner: root
                    group: root
                    """)
        self.failUnlessExists("/etc/templated")

    def test_create_file_template_with_extends(self):
        self.chroot.check_apply("""
            resources:
                - File:
                    name: /etc/templated
                    template: {{ "package://yaybu.tests/assets/template_with_extends.j2" }}
                    template_args:
                        foo: this is foo
                        bar: 42
                    owner: root
                    group: root
                    """)
        self.failUnlessExists("/etc/templated")
        with self.chroot.open("/etc/templated") as fp:
            self.failUnless("this is foo" in fp.read())

    def test_modify_file(self):
        with self.chroot.open("/etc/test_modify_file", "w") as fp:
            fp.write("foo\nbar\nbaz")

        self.chroot.check_apply("""
            resources:
                - File:
                    name: /etc/test_modify_file
                    template: {{ "package://yaybu.tests/assets/template1.j2" }}
                    template_args:
                        foo: this is a modified file
                        bar: 37
            """)

    def test_remove_file(self):
        self.chroot.check_apply("""
            resources:
              - File:
                  name: /etc/toremove
            """)
        self.chroot.check_apply("""
            resources:
              - File:
                  name: /etc/toremove
                  policy: remove
            """)
        self.failIfExists("/etc/toremove")


    def test_empty(self):
        with self.chroot.open("/etc/foo", "w") as fp:
            fp.write("foo")

        self.chroot.check_apply("""
            resources:
                - File:
                    name: /etc/foo
            """)

    def test_empty_nochange(self):
        with self.chroot.open("/etc/foo", "w") as fp:
            fp.write("")
        os.chmod(self.chroot._enpathinate("/etc/foo"), 0644)

        self.assertRaises(error.NothingChanged, self.chroot.apply, """
            resources:
                - File:
                    name: /etc/foo
            """)

    def test_carriage_returns(self):
        """ a template that does not end in \n will still result in a file ending in \n """
        with self.chroot.open("/etc/test_carriage_returns", "w") as fp:
            fp.write("foo\n")
        os.chmod(self.chroot._enpathinate("/etc/test_carriage_returns"), 0644)

        self.assertRaises(error.NothingChanged, self.chroot.apply, """
            resources:
                - File:
                    name: /etc/test_carriage_returns
                    template: {{ "package://yaybu.tests/assets/test_carriage_returns.j2" }}
                    """)

    def test_carriage_returns2(self):
        """ a template that does end in \n will not gain an extra \n in the resulting file"""
        with self.chroot.open("/etc/test_carriage_returns2", "w") as fp:
            fp.write("foo\n")
        os.chmod(self.chroot._enpathinate("/etc/test_carriage_returns2"), 0644)

        self.assertRaises(error.NothingChanged, self.chroot.apply, """
            resources:
                - File:
                    name: /etc/test_carriage_returns2
                    template: {{ "package://yaybu.tests/assets/test_carriage_returns2.j2" }}
            """)

    def test_unicode(self):
        self.chroot.check_apply(open(sibpath("assets/unicode1.yay")).read())

    def test_static(self):
        """ Test setting the contents to that of a static file. """
        self.chroot.check_apply("""
            resources:
                - File:
                    name: /etc/foo
                    static: {{ "package://yaybu.tests/assets/test_carriage_returns2.j2" }}
            """)

    def test_static_empty(self):
        self.chroot.check_apply("""
            resources:
                - File:
                    name: /etc/foo
                    static: {{ "package://yaybu.tests/assets/empty_file" }}
            """)

    def test_missing(self):
        """ Test trying to use a file that isn't in the yaybu path """
        self.assertRaises(error.MissingAsset, self.chroot.apply, """
            resources:
                - File:
                    name: /etc/foo
                    static: this-doesnt-exist
            """)


class TestFileRemove(TestCase):

    def test_remove(self):
        """ Test removing a file that exists. """
        with self.chroot.open("/etc/bar","w") as fp:
            fp.write("")

        self.chroot.check_apply("""
            resources:
                - File:
                    name: /etc/bar
                    policy: remove
            """)

    def test_remove_missing(self):
        """ Test removing a file that does not exist. """
        self.failIfExists("/etc/baz")
        self.assertRaises(error.NothingChanged, self.chroot.apply, """
            resources:
                - File:
                    name: /etc/baz
                    policy: remove
            """)

    def test_remove_notafile(self):
        """ Test removing something that is not a file. """
        self.chroot.mkdir("/etc/qux")
        self.assertRaises(error.InvalidProvider, self.chroot.apply, """
            resources:
                - File:
                    name: /etc/qux
                    policy: remove
            """)

