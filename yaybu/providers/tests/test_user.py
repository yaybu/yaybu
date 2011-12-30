import os, shutil

from yaybu.harness import FakeChrootTestCase
from yaybu.util import sibpath
from yaybu.core import error


class TestUser(FakeChrootTestCase):

    def test_simple_user(self):
        self.fixture.check_apply("""
            resources:
                - User:
                    name: test
            """)

    def test_disabled_login(self):
        self.fixture.check_apply("""
            resources:
                - User:
                    - name: test
                      disabled-login: True
            """)
        rv = self.fixture.apply("""
            resources:
                - User:
                    - name: test
                      disabled-login: True
            """)
        self.assertEqual(rv, 254)

    def test_user_with_home(self):
        self.fixture.check_apply("""
            resources:
                - User:
                    name: test
                    home: /home/foo
            """)

    def test_user_with_impossible_home(self):
        rv = self.fixture.apply("""
            resources:
                - User:
                    name: test
                    home: /does/not/exist
            """)
        self.assertEqual(rv, error.UserAddError.returncode)

    def test_user_with_uid(self):
        self.fixture.check_apply("""
            resources:
                - User:
                    name: test
                    uid: 1111
            """)

    def test_user_with_gid(self):
        self.fixture.check_apply("""
            resources:
                - Group:
                    name: testgroup
                    gid: 1111
                - User:
                    name: test
                    gid: 1111
            """)

    def test_user_with_fullname(self):
        self.fixture.check_apply("""
            resources:
                - User:
                    name: test
                    fullname: testy mctest
            """)

    def test_user_with_password(self):
        self.fixture.check_apply("""
            resources:
                - User:
                    name: test
                    password: password
            """)

    def test_user_with_group(self):
        self.fixture.check_apply("""
            resources:
                - User:
                    name: test
                    group: nogroup
            """)

    def test_user_with_groups(self):
        self.fixture.check_apply("""
            resources:
                - User:
                    name: test
                    groups:
                        - nogroup
            """)

    def test_user_with_groups_replace(self):
        self.fixture.check_apply("""
            resources:
                - User:
                    name: test
                    groups:
                        - nogroup
                    append: False
            """)


class TestUserRemove(FakeChrootTestCase):

    def test_remove_existing(self):
        self.failUnless(self.fixture.get_user("nobody"))

        self.fixture.check_apply("""
            resources:
                - User:
                    name: nobody
                    policy: remove
            """)

        self.failUnlessRaises(KeyError, self.fixture.get_user, "nobody")

    def test_remove_non_existing(self):
        self.failUnlessRaises(KeyError, self.fixture.get_user, "zzidontexistzz")

        rv = self.fixture.apply("""
            resources:
                - User:
                    name: zzidontexistzz
                    policy: remove
            """)

        self.failUnlessEqual(rv, 254)

        self.failUnlessRaises(KeyError, self.fixture.get_user, "zzidontexistzz")

