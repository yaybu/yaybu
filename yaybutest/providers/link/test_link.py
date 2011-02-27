
import os
from yaybutest.utils import TestCase
from yaybu.core import error


class TestLink(TestCase):

    def test_create_link(self):
        rv = self.apply("""
            resources:
              - Link:
                  name: /etc/somelink
                  to: /etc
                  owner: root
                  group: root
            """)

        self.failUnless(rv == 0)
        self.failUnlessExists("/etc/somelink")

    def test_remove_link(self):
        os.system("ln -s / %s" % self.enpathinate("/etc/toremovelink"))
        rv = self.apply("""
            resources:
              - Link:
                  name: /etc/toremovelink
                  policy: remove
            """)
        self.failUnless(rv == 0)
        self.failUnless(not os.path.exists(self.enpathinate("/etc/toremovelink")))


    def test_already_exists(self):
        os.system("ln -s / %s" % self.enpathinate("/etc/existing"))
        rv = self.apply("""
            resources:
              - Link:
                  name: /etc/existing
                  to: /
        """)
        self.failUnless(rv == 0)

    def test_dangling(self):
        rv = self.apply("""
        resources:
             - Link:
                 name: /etc/test_dangling
                 to: /etc/not_there
        """)
        self.failUnless(rv == error.DanglingSymlink.returncode)
