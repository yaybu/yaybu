
import os
from yaybu.provisioner.tests.fixture import TestCase
from yaybu.core import error

def sibpath(filename):
    return os.path.join(os.path.dirname(__file__), filename)


class TestLink(TestCase):

    def test_create_link(self):
        self.chroot.check_apply("""
            resources:
              - Link:
                  name: /etc/somelink
                  to: /etc
                  owner: root
                  group: root
            """)

        self.failUnlessExists("/etc/somelink")

    def test_remove_link(self):
        self.chroot.symlink("/", "/etc/toremovelink")
        rv = self.chroot.check_apply("""
            resources:
              - Link:
                  name: /etc/toremovelink
                  policy: remove
            """)
        self.failIfExists("/etc/toremovelink")

    def test_already_exists(self):
        self.chroot.symlink("/", "/etc/existing")
        self.assertRaises(error.NothingChanged, self.chroot.apply, """
            resources:
              - Link:
                  name: /etc/existing
                  to: /
        """)
        self.failUnlessEqual(self.chroot.readlink("/etc/existing"), "/")

    def test_already_exists_notalink(self):
        """ Test for the path already existing but is not a link. """
        with self.chroot.open("/bar_notalink", "w") as fp:
            fp.write("")
        with self.chroot.open("/foo", "w") as fp:
            fp.write("")

        self.chroot.check_apply("""
            resources:
                - Link:
                    name: /bar_notalink
                    to: /foo
            """)

        self.failUnlessEqual(self.chroot.readlink("/bar_notalink"), "/foo")

    def test_already_exists_pointing_elsewhere(self):
        """ Test for the path already existing but being a link to somewhere else. """
        self.chroot.touch("/baz")
        self.chroot.touch("/foo")
        self.chroot.symlink("/baz", "/bar_elsewhere")
        self.chroot.check_apply("""
            resources:
                - Link:
                    name: /bar_elsewhere
                    to: /foo
            """)
        self.failUnlessEqual(self.chroot.readlink("/bar_elsewhere"), "/foo")

    def test_dangling(self):
        self.assertRaises(error.DanglingSymlink, self.chroot.apply, """
        resources:
             - Link:
                 name: /etc/test_dangling
                 to: /etc/not_there
        """)

    def test_unicode(self):
        self.chroot.check_apply(open(sibpath("link_unicode1.yay")).read())

