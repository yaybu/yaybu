
import os
from yaybu.harness import FakeChrootTestCase
from yaybu.core import error

def sibpath(filename):
    return os.path.join(os.path.dirname(__file__), filename)


class TestLink(FakeChrootTestCase):

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
        self.fixture.symlink("/", "/etc/toremovelink")
        rv = self.fixture.check_apply("""
            resources:
              - Link:
                  name: /etc/toremovelink
                  policy: remove
            """)
        self.failIfExists("/etc/toremovelink")

    def test_already_exists(self):
        self.fixture.symlink("/", "/etc/existing")
        rv = self.fixture.apply("""
            resources:
              - Link:
                  name: /etc/existing
                  to: /
        """)
        self.assertEqual(rv, 254)
        self.failUnlessEqual(self.fixture.readlink("/etc/existing"), "/")

    def test_already_exists_notalink(self):
        """ Test for the path already existing but is not a link. """
        with self.fixture.open("/bar_notalink", "w") as fp:
            fp.write("")
        with self.fixture.open("/foo", "w") as fp:
            fp.write("")

        self.fixture.check_apply("""
            resources:
                - Link:
                    name: /bar_notalink
                    to: /foo
            """)

        self.failUnlessEqual(self.fixture.readlink("/bar_notalink"), "/foo")

    def test_already_exists_pointing_elsewhere(self):
        """ Test for the path already existing but being a link to somewhere else. """
        self.fixture.touch("/baz")
        self.fixture.touch("/foo")
        self.fixture.symlink("/baz", "/bar_elsewhere")
        self.fixture.check_apply("""
            resources:
                - Link:
                    name: /bar_elsewhere
                    to: /foo
            """)
        self.failUnlessEqual(self.fixture.readlink("/bar_elsewhere"), "/foo")

    def test_dangling(self):
        rv = self.fixture.apply("""
        resources:
             - Link:
                 name: /etc/test_dangling
                 to: /etc/not_there
        """)
        self.assertEqual(rv, error.DanglingSymlink.returncode)

    def test_unicode(self):
        self.fixture.check_apply(open(sibpath("link_unicode1.yay")).read())

