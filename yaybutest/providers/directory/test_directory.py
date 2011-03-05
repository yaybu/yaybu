# coding: utf-8

import os
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

    def test_unicode(self):
        self.check_apply(open(sibpath("unicode1.yay")).read())
        self.failUnless(os.path.isdir(self.enpathinate("/etc/££££££")))
