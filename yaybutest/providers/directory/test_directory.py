# coding=utf-8

import os
import pwd
import grp
import stat
from yaybutest.utils import TestCase


def sibpath(filename):
    return os.path.join(os.path.dirname(__file__), filename)


class TestDirectory(TestCase):

    def test_create_directory(self):
        self.check_apply("""
            resources:
              - Directory:
                  name: /etc/somedir
                  owner: root
                  group: root
            """)
        self.failUnlessExists("/etc/somedir")
        path = self.enpathinate("/etc/somedir")
        self.failUnless(os.path.isdir(path))

    def test_create_directory_and_parents(self):
        self.check_apply("""
            resources:
                - Directory:
                    name: /etc/foo/bar/baz
                    parents: True
            """)
        self.failUnless(os.path.isdir(self.enpathinate("/etc/foo/bar/baz")))

    def test_remove_directory(self):
        os.mkdir(self.enpathinate("/etc/somedir"))
        self.check_apply("""
            resources:
              - Directory:
                  name: /etc/somedir
                  policy: remove
        """)

    def test_remove_directory_recursive(self):
        os.mkdir(self.enpathinate("/etc/somedir"))
        open(self.enpathinate("/etc/somedir/child"), "w").write("")
        self.check_apply("""
            resources:
                - Directory:
                    name: /etc/somedir
                    policy: remove-recursive
            """)
        self.failUnless(not os.path.exists(self.enpathinate("/etc/somedir")))

    def test_unicode(self):
        utf8 = "/etc/£££££" # this is utf-8 encoded
        self.check_apply(open(sibpath("unicode1.yay")).read())
        self.failUnless(os.path.exists(self.enpathinate(utf8)))

    def test_attributes(self):
        self.check_apply("""
            resources:
              - Directory:
                  name: /etc/somedir2
                  owner: nobody
                  group: nogroup
                  mode: 0777
            """)
        self.failUnlessExists("/etc/somedir2")
        st = os.stat(self.enpathinate("/etc/somedir2"))
        self.failUnless(pwd.getpwuid(st.st_uid)[0] != 'nobody')
        self.failUnless(grp.getgrgid(st.st_gid)[0] != 'nogroup')
        mode = stat.S_IMODE(st.st_mode)
        self.assertEqual(mode, 0777)
