from yaybu.harness import FakeChrootTestCase
from yaybu.core.error import MissingDependency

class RsyncTest(FakeChrootTestCase):
    """
    Test the rsync checkout provider.

    To run these tests, rsync must be installed in the test environment.
    """

    def setUp(self):
        super(RsyncTest, self).setUp()
        self.sync()

    def sync(self, expect=0):
        return self.fixture.check_apply("""
            resources:
                - Package:
                    name: rsync
                - Directory:
                  - name: /source
                    mode: 0755
                - Checkout:
                    scm: rsync
                    name: /dest
                    repository: /source
            """, expect=expect)


    def test_add(self):
        self.fixture.touch("/source/a")
        self.sync()
        self.failUnless(self.fixture.exists("/dest/a"))

    def test_del(self):
        self.fixture.touch("/dest/b")
        self.sync()
        self.failUnless(not self.fixture.exists("/dest/b"))

    def test_nochange(self):
        self.sync(expect=254)


class RsyncMissingTest(FakeChrootTestCase):

    def test_missing_rsync(self):
        rv = self.fixture.apply("""
           resources:
               - Checkout:
                   scm: rsync
                   name: /dest
                   repository: /source
           """)
        self.assertEqual(MissingDependency.returncode, rv)

