from yaybutest.utils import TestCase
from yaybu.core import error
import pwd
import grp
import os
import stat
import errno

def sibpath(filename):
    return os.path.join(os.path.dirname(__file__), filename)

class TestFileApply(TestCase):

    def test_create_missing_component(self):
        rv = self.apply("""
            resources:
              - File:
                  name: /etc/missing/filename
            """)
        self.assertEqual(rv, error.PathComponentMissing.returncode)

    def test_create_missing_component_simulate(self):
        rv = self.apply_simulate("""
            resources:
              - File:
                  name: /etc/missing/filename
            """)
        self.assertEqual(rv, error.PathComponentMissing.returncode)

    def test_create_file(self):
        self.check_apply("""
            resources:
              - File:
                  name: /etc/somefile
                  owner: root
                  group: root
            """)

        self.failUnlessExists("/etc/somefile")

    def test_attributes(self):
        self.check_apply("""
            resources:
              - File:
                  name: /etc/somefile2
                  owner: nobody
                  group: nogroup
                  mode: 0666
            """)
        self.failUnlessExists("/etc/somefile2")
        st = os.stat(self.enpathinate("/etc/somefile2"))
        self.failUnless(pwd.getpwuid(st.st_uid)[0] != 'nobody')
        self.failUnless(grp.getgrgid(st.st_gid)[0] != 'nogroup')
        mode = stat.S_IMODE(st.st_mode)
        self.assertEqual(mode, 0666)

    def test_create_file_template(self):
        self.check_apply("""
            resources:
                - File:
                    name: /etc/templated
                    template: package://yaybutest.providers.file/template1.j2
                    template_args:
                        foo: this is foo
                        bar: 42
                    owner: root
                    group: root
                    """)
        self.failUnlessExists("/etc/templated")

    def test_remove_file(self):
        self.check_apply("""
            resources:
              - File:
                  name: /etc/toremove
            """)
        self.check_apply("""
            resources:
              - File:
                  name: /etc/toremove
                  policy: remove
            """)
        self.failUnless(not os.path.exists(self.enpathinate("/etc/toremove")))


    def test_empty(self):
        open(self.enpathinate("/etc/foo"), "w").write("foo")
        self.check_apply("""
            resources:
                - File:
                    name: /etc/foo
            """)

    def test_empty_nochange(self):
        open(self.enpathinate("/etc/foo"), "w").write("")
        rv = self.apply("""
            resources:
                - File:
                    name: /etc/foo
            """)
        self.assertEqual(rv, 255)


    def test_carriage_returns(self):
        """ a template that does not end in \n will still result in a file ending in \n """
        open(self.enpathinate("/etc/test_carriage_returns"), "w").write("foo\n")
        rv = self.apply("""
            resources:
                - File:
                    name: /etc/test_carriage_returns
                    template: package://yaybutest.providers.file/test_carriage_returns.j2
            """)
        self.assertEqual(rv, 255) # nothing changed

    def test_carriage_returns2(self):
        """ a template that does end in \n will not gain an extra \n in the resulting file"""
        open(self.enpathinate("/etc/test_carriage_returns2"), "w").write("foo\n")
        rv = self.apply("""
            resources:
                - File:
                    name: /etc/test_carriage_returns2
                    template: package://yaybutest.providers.file/test_carriage_returns2.j2
            """)
        self.assertEqual(rv, 255) # nothing changed

    def test_unicode(self):
        self.check_apply(open(sibpath("unicode1.yay")).read())

    def test_static(self):
        """ Test setting the contents to that of a static file. """
        self.check_apply("""
            resources:
                - File:
                    name: /etc/foo
                    static: package://yaybutest.providers.file/test_carriage_returns2.j2
            """)


class TestFileRemove(TestCase):

    def test_remove(self):
        """ Test removing a file that exists. """
        open(self.enpathinate("/etc/bar"),"w").write("")
        self.check_apply("""
            resources:
                - File:
                    name: /etc/bar
                    policy: remove
            """)

    def test_remove_missing(self):
        """ Test removing a file that does not exist. """
        self.failUnless(not os.path.exists(self.enpathinate("/etc/baz")))
        rv = self.apply("""
            resources:
                - File:
                    name: /etc/baz
                    policy: remove
            """)
        self.failUnlessEqual(rv, 255)

    def test_remove_notafile(self):
        """ Test removing something that is not a file. """
        os.mkdir(self.enpathinate("/etc/qux"))
        rv = self.apply("""
            resources:
                - File:
                    name: /etc/qux
                    policy: remove
            """)
        self.failUnlessEqual(rv, 139)

