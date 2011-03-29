
import os
from yaybutest.utils import TestCase
from yaybu.core import error

def sibpath(filename):
    return os.path.join(os.path.dirname(__file__), filename)


class TestLink(TestCase):

    def test_create_link(self):
        self.check_apply("""
            resources:
              - Link:
                  name: /etc/somelink
                  to: /etc
                  owner: root
                  group: root
            """)

        self.failUnlessExists("/etc/somelink")

    def test_remove_link(self):
        os.system("ln -s / %s" % self.enpathinate("/etc/toremovelink"))
        rv = self.check_apply("""
            resources:
              - Link:
                  name: /etc/toremovelink
                  policy: remove
            """)
        self.failUnless(not os.path.exists(self.enpathinate("/etc/toremovelink")))


    def test_already_exists(self):
        os.system("ln -s %s %s" % (self.enpathinate("/"), self.enpathinate("/etc/existing")))
        rv = self.apply("""
            resources:
              - Link:
                  name: /etc/existing
                  to: /
        """)
        self.assertEqual(rv, 255)
        self.failUnlessEqual(os.readlink(self.enpathinate("/etc/existing")), self.enpathinate("/"))

    def test_already_exists_notalink(self):
        """ Test for the path already existing but is not a link. """
        open(self.enpathinate("/bar_notalkink"), "w").write("")
        open(self.enpathinate("/foo"), "w").write("")
        self.check_apply("""
            resources:
                - Link:
                    name: /bar_notalink
                    to: /foo
            """)
        self.failUnlessEqual(os.readlink(self.enpathinate("/bar_notalink")), self.enpathinate("/foo"))

    def test_already_exists_pointing_elsewhere(self):
        """ Test for the path already existing but being a link to somewhere else. """
        open(self.enpathinate("/baz"), "w").write("")
        open(self.enpathinate("/foo"), "w").write("")
        os.symlink(self.enpathinate("/baz"), self.enpathinate("/bar_elsewhere"))
        self.check_apply("""
            resources:
                - Link:
                    name: /bar_elsewhere
                    to: /foo
            """)
        self.failUnlessEqual(os.readlink(self.enpathinate("/bar_elsewhere")), self.enpathinate("/foo"))

    def test_dangling(self):
        rv = self.apply("""
        resources:
             - Link:
                 name: /etc/test_dangling
                 to: /etc/not_there
        """)
        self.assertEqual(rv, error.DanglingSymlink.returncode)

    def test_unicode(self):
        self.check_apply(open(sibpath("unicode1.yay")).read())
