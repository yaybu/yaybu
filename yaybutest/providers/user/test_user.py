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

