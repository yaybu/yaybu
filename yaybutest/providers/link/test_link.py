
import os
from yaybutest.utils import TestCase
from yaybu.core import error

def sibpath(filename):
    return os.path.join(os.path.dirname(__file__), filename)


class TestLink(TestCase):

    def test_create_link(self):
        self.fixture.check_apply("""
            resources:
              - Link:
                  name: /etc/somelink
                  to: /etc
                  owner: root
                  group: root
            """)

        self.failUnlessExists("/etc/somelink")

    def test_remove_link(self):
        os.system("ln -s / %s" % self.fixture.enpathinate("/etc/toremovelink"))
        rv = self.fixture.check_apply("""
            resources:
              - Link:
                  name: /etc/toremovelink
                  policy: remove
            """)
        self.failUnless(not os.path.exists(self.fixture.enpathinate("/etc/toremovelink")))


    def test_already_exists(self):
        os.system("ln -s %s %s" % (self.fixture.enpathinate("/"), self.fixture.enpathinate("/etc/existing")))
        rv = self.fixture.apply("""
            resources:
              - Link:
                  name: /etc/existing
                  to: /
        """)
        self.assertEqual(rv, 255)
        self.failUnlessEqual(os.readlink(self.fixture.enpathinate("/etc/existing")), self.fixture.enpathinate("/"))

    def test_already_exists_notalink(self):
        """ Test for the path already existing but is not a link. """
        with self.fixture.open("/bar_notalink", "w") as fp:
            fp.write("")
        with self.fixture.open("/foo", "w") as fp:
            fp.write("")

        # 142
        self.fixture.check_apply("""
            resources:
                - Link:
                    name: /bar_notalink
                    to: /foo
            """)
        self.failUnlessEqual(os.readlink(self.fixture.enpathinate("/bar_notalink")), self.fixture.enpathinate("/foo"))

    def test_already_exists_pointing_elsewhere(self):
        """ Test for the path already existing but being a link to somewhere else. """
        open(self.fixture.enpathinate("/baz"), "w").write("")
        open(self.fixture.enpathinate("/foo"), "w").write("")
        os.symlink(self.fixture.enpathinate("/baz"), self.fixture.enpathinate("/bar_elsewhere"))
        self.fixture.check_apply("""
            resources:
                - Link:
                    name: /bar_elsewhere
                    to: /foo
            """)
        self.failUnlessEqual(os.readlink(self.fixture.enpathinate("/bar_elsewhere")), self.fixture.enpathinate("/foo"))

    def test_dangling(self):
        rv = self.fixture.apply("""
        resources:
             - Link:
                 name: /etc/test_dangling
                 to: /etc/not_there
        """)
        self.assertEqual(rv, error.DanglingSymlink.returncode)

    def test_unicode(self):
        self.fixture.check_apply(open(sibpath("unicode1.yay")).read())

