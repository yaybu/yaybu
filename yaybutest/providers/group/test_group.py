import os, shutil, grp

from yaybutest.utils import TestCase
from yaybu.util import sibpath


class TestGroup(TestCase):

    def test_simple_group(self):
        self.check_apply("""
            resources:
                - Group:
                    name: test
            """)

        self.failUnless(self.get_group("test"))

    def test_group_with_gid(self):
        self.check_apply("""
            resources:
                - Group:
                    name: test
                    gid: 1111
            """)

        self.failUnless(self.get_group("test"))

    def test_existing_group(self):
        """ Test creating a group whose name already exists. """

        self.failUnless(self.get_group("users"))

        rv = self.apply("""
            resources:
                - Group:
                    name: users
            """)

        self.failUnlessEqual(rv, 255)

        self.failUnless(self.get_group("users"))

    def test_existing_gid(self):
        """ Test creating a group whose specified gid already exists. """
        rv = self.apply("""
            resources:
                - Group:
                    name: test
                    gid: 100
            """)

        self.failUnlessEqual(rv, 4)
        self.failUnlessRaises(KeyError, self.get_group, "test")


class TestGroupRemove(TestCase):

    def test_remove_existing(self):
        self.failUnless(self.get_group("users"))

        self.check_apply("""
            resources:
                - Group:
                    name: users
                    policy: remove
            """)

        self.failUnlessRaises(KeyError, self.get_group, "users")

    def test_remove_non_existing(self):
        self.failUnlessRaises(KeyError, self.get_group, "zzidontexistzz")

        rv = self.apply("""
            resources:
                - Group:
                    name: zzidontexistzz
                    policy: remove
            """)

        self.failUnlessEqual(rv, 255)

        self.failUnlessRaises(KeyError, self.get_group, "zzidontexistzz")


