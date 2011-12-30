from yaybu.harness import FakeChrootTestCase
from yaybu.core import error
import pwd
import grp
import os
import stat
import errno

def sibpath(filename):
    return os.path.join(os.path.dirname(__file__), filename)

class TestFileApply(FakeChrootTestCase):

    def test_create_missing_component(self):
        rv = self.fixture.apply("""
            resources:
              - File:
                  name: /etc/missing/filename
            """)
        self.assertEqual(rv, error.PathComponentMissing.returncode)

    def test_create_missing_component_simulate(self):
        """
        Right now we treat missing directories as a warning in simulate mode, as other outside processes might have created them.
        Later on we might not generate warnings for resources we can see will be created
        """
        rv = self.fixture.apply_simulate("""
            resources:
              - File:
                  name: /etc/missing/filename
            """)
        self.assertEqual(rv, 0)

    def test_create_file(self):
        self.fixture.check_apply("""
            resources:
              - File:
                  name: /etc/somefile
                  owner: root
                  group: root
            """)

        self.failUnlessExists("/etc/somefile")

    def test_attributes(self):
        self.fixture.check_apply("""
            resources:
              - File:
                  name: /etc/somefile2
                  owner: nobody
                  group: nogroup
                  mode: 0666
            """)
        self.failUnlessExists("/etc/somefile2")
        st = self.fixture.stat("/etc/somefile2")
        self.failUnless(pwd.getpwuid(st.st_uid)[0] != 'nobody')
        self.failUnless(grp.getgrgid(st.st_gid)[0] != 'nogroup')
        mode = stat.S_IMODE(st.st_mode)
        self.assertEqual(mode, 0666)

    def test_create_file_template(self):
        self.fixture.check_apply("""
            resources:
                - File:
                    name: /etc/templated
                    template: package://yaybu.providers.tests/template1.j2
                    template_args:
                        foo: this is foo
                        bar: 42
                    owner: root
                    group: root
                    """)
        self.failUnlessExists("/etc/templated")

    def test_create_file_template_with_extends(self):
        self.fixture.check_apply("""
            resources:
                - File:
                    name: /etc/templated
                    template: package://yaybu.providers.tests/template_with_extends.j2
                    template_args:
                        foo: this is foo
                        bar: 42
                    owner: root
                    group: root
                    """)
        self.failUnlessExists("/etc/templated")
        with self.fixture.open("/etc/templated") as fp:
            self.failUnless("this is foo" in fp.read())

    def test_modify_file(self):
        with self.fixture.open("/etc/test_modify_file", "w") as fp:
          fp.write("foo\nbar\nbaz")

        self.fixture.check_apply("""
            resources:
                - File:
                    name: /etc/test_modify_file
                    template: package://yaybu.providers.tests/template1.j2
                    template_args:
                        foo: this is a modified file
                        bar: 37
            """)

    def test_remove_file(self):
        self.fixture.check_apply("""
            resources:
              - File:
                  name: /etc/toremove
            """)
        self.fixture.check_apply("""
            resources:
              - File:
                  name: /etc/toremove
                  policy: remove
            """)
        self.failIfExists("/etc/toremove")


    def test_empty(self):
        with self.fixture.open("/etc/foo", "w") as fp:
            fp.write("foo")

        self.fixture.check_apply("""
            resources:
                - File:
                    name: /etc/foo
            """)

    def test_empty_nochange(self):
        with self.fixture.open("/etc/foo", "w") as fp:
            fp.write("")

        rv = self.fixture.apply("""
            resources:
                - File:
                    name: /etc/foo
            """)
        self.assertEqual(rv, 254)


    def test_carriage_returns(self):
        """ a template that does not end in \n will still result in a file ending in \n """
        with self.fixture.open("/etc/test_carriage_returns", "w") as fp:
            fp.write("foo\n")

        rv = self.fixture.apply("""
            resources:
                - File:
                    name: /etc/test_carriage_returns
                    template: package://yaybu.providers.tests/test_carriage_returns.j2
            """)
        self.assertEqual(rv, 254) # nothing changed

    def test_carriage_returns2(self):
        """ a template that does end in \n will not gain an extra \n in the resulting file"""
        with self.fixture.open("/etc/test_carriage_returns2", "w") as fp:
            fp.write("foo\n")

        rv = self.fixture.apply("""
            resources:
                - File:
                    name: /etc/test_carriage_returns2
                    template: package://yaybu.providers.tests/test_carriage_returns2.j2
            """)
        self.assertEqual(rv, 254) # nothing changed

    def test_unicode(self):
        self.fixture.check_apply(open(sibpath("unicode1.yay")).read())

    def test_static(self):
        """ Test setting the contents to that of a static file. """
        self.fixture.check_apply("""
            resources:
                - File:
                    name: /etc/foo
                    static: package://yaybu.providers.tests/test_carriage_returns2.j2
            """)

    def test_missing(self):
        """ Test trying to use a file that isn't in the yaybu path """
        rv = self.fixture.apply("""
            resources:
                - File:
                    name: /etc/foo
                    static: this-doesnt-exist
            """)
        self.failUnlessEqual(rv, error.MissingAsset.returncode)


class TestFileRemove(FakeChrootTestCase):

    def test_remove(self):
        """ Test removing a file that exists. """
        with self.fixture.open("/etc/bar","w") as fp:
            fp.write("")

        self.fixture.check_apply("""
            resources:
                - File:
                    name: /etc/bar
                    policy: remove
            """)

    def test_remove_missing(self):
        """ Test removing a file that does not exist. """
        self.failIfExists("/etc/baz")
        rv = self.fixture.apply("""
            resources:
                - File:
                    name: /etc/baz
                    policy: remove
            """)
        self.failUnlessEqual(rv, 254)

    def test_remove_notafile(self):
        """ Test removing something that is not a file. """
        self.fixture.mkdir("/etc/qux")
        rv = self.fixture.apply("""
            resources:
                - File:
                    name: /etc/qux
                    policy: remove
            """)
        self.failUnlessEqual(rv, 139)

