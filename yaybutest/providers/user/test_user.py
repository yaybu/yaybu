import os, shutil

from yaybutest.utils import TestCase
from yaybu.util import sibpath
from yaybu.core import error


class TestUser(TestCase):

    def test_simple_user(self):
        self.check_apply("""
            resources:
                - User:
                    name: test
            """)

    def test_user_with_home(self):
        self.check_apply("""
            resources:
                - User:
                    name: test
                    home: /home/foo
            """)

    def test_user_with_impossible_home(self):
        rv = self.apply("""
            resources:
                - User:
                    name: test
                    home: /does/not/exist
            """)
        self.failUnless(rv == error.UserAddError.returncode)

    def test_user_with_uid(self):
        self.check_apply("""
            resources:
                - User:
                    name: test
                    uid: 1111
            """)

    def test_user_with_gid(self):
        self.check_apply("""
            resources:
                - Group:
                    name: testgroup
                    gid: 1111
                - User:
                    name: test
                    gid: 1111
            """)

    def test_user_with_fullname(self):
        self.check_apply("""
            resources:
                - User:
                    name: test
                    fullname: testy mctest
            """)

    def test_user_with_password(self):
        self.check_apply("""
            resources:
                - User:
                    name: test
                    password: password
            """)

