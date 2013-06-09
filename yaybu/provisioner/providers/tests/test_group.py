import os, shutil, grp

from yaybu.provisioner.tests.fixture import TestCase
from yaybu.util import sibpath


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

        rv = self.chroot.apply("""
            resources:
                - Group:
                    name: users
            """)

        self.failUnlessEqual(rv, 254)

        self.failUnless(self.chroot.get_group("users"))

    def test_existing_gid(self):
        """ Test creating a group whose specified gid already exists. """
        rv = self.chroot.apply("""
            resources:
                - Group:
                    name: test
                    gid: 100
            """)

        self.failUnlessEqual(rv, 140)
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

        rv = self.chroot.apply("""
            resources:
                - Group:
                    name: zzidontexistzz
                    policy: remove
            """)

        self.failUnlessEqual(rv, 254)

        self.failUnlessRaises(KeyError, self.chroot.get_group, "zzidontexistzz")


