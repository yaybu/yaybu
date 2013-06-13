import os, shutil

from yaybu.provisioner.tests.fixture import TestCase
from yaybu.util import sibpath
from yaybu.core import error


class TestUser(TestCase):

    def test_simple_user(self):
        self.chroot.check_apply("""
            resources:
                - User:
                    name: test
            """)

    def test_disabled_login(self):
        self.chroot.check_apply("""
            resources:
                - User:
                    - name: test
                      disabled_login: True
            """)
        self.assertRaises(error.NothingChanged, self.chroot.apply, """
            resources:
                - User:
                    - name: test
                      disabled_login: True
            """)

    def test_user_with_home(self):
        self.chroot.check_apply("""
            resources:
                - User:
                    name: test
                    home: /home/foo
            """)

    def test_user_with_impossible_home(self):
        self.assertRaises(error.UserAddError, self.chroot.apply, """
            resources:
                - User:
                    name: test
                    home: /does/not/exist
            """)

    def test_user_with_uid(self):
        self.chroot.check_apply("""
            resources:
                - User:
                    name: test
                    uid: 1111
            """)

    def test_user_with_gid(self):
        self.chroot.check_apply("""
            resources:
                - Group:
                    name: testgroup
                    gid: 1111
                - User:
                    name: test
                    gid: 1111
            """)

    def test_user_with_fullname(self):
        self.chroot.check_apply("""
            resources:
                - User:
                    name: test
                    fullname: testy mctest
            """)

    def test_user_with_password(self):
        self.chroot.check_apply("""
            resources:
                - User:
                    name: test
                    password: password
            """)

    def test_user_with_group(self):
        self.chroot.check_apply("""
            resources:
                - User:
                    name: test
                    group: nogroup
            """)

    def test_user_with_groups(self):
        self.chroot.check_apply("""
            resources:
                - User:
                    name: test
                    groups:
                        - nogroup
            """)

    def test_user_with_groups_replace(self):
        self.chroot.check_apply("""
            resources:
                - User:
                    name: test
                    groups:
                        - nogroup
                    append: False
            """)


class TestUserRemove(TestCase):

    def test_remove_existing(self):
        self.failUnless(self.chroot.get_user("nobody"))

        self.chroot.check_apply("""
            resources:
                - User:
                    name: nobody
                    policy: remove
            """)

        self.failUnlessRaises(KeyError, self.chroot.get_user, "nobody")

    def test_remove_non_existing(self):
        self.failUnlessRaises(KeyError, self.chroot.get_user, "zzidontexistzz")

        self.assertRaises(error.NothingChanged, self.chroot.apply, """
            resources:
                - User:
                    name: zzidontexistzz
                    policy: remove
            """)

        self.failUnlessRaises(KeyError, self.chroot.get_user, "zzidontexistzz")

