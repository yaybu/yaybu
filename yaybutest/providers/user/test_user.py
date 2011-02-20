import os, shutil

from yaybutest.utils import TestCase
from yaybu.util import sibpath


class TestUser(TestCase):

    def test_simple_user(self):
        self.apply("""
            resources:
                - User:
                    name: test
            """)

    def test_user_with_home(self):
        self.apply("""
            resources:
                - User:
                    name: test
                    home: /home/foo
            """)

    def test_user_with_uid(self):
        self.apply("""
            resources:
                - User:
                    name: test
                    uid: 1111
            """)

    #def test_user_with_gid(self):
    #    self.apply("""
    #        resources:
    #            - User:
    #                name: test
    #                gid: 1111
    #        """)

    def test_user_with_fullname(self):
        self.apply("""
            resources:
                - User:
                    name: test
                    fullname: testy mctest
            """)

    def test_user_with_password(self):
        self.apply("""
            resources:
                - User:
                    name: test
                    password: password
            """)

