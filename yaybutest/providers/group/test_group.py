import os, shutil

from yaybutest.utils import TestCase
from yaybu.util import sibpath


class TestGroup(TestCase):

    def test_simple_group(self):
        self.check_apply("""
            resources:
                - Group:
                    name: test
            """)

    def test_group_with_gid(self):
        self.check_apply("""
            resources:
                - Group:
                    name: test
                    gid: 1111
            """)

