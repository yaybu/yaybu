from yaybu.parts.provisioner.tests.harness import FakeChrootTestCase
from yaybu.core.error import MissingDependency


class SubversionMissingTest(FakeChrootTestCase):

    def test_missing_svn(self):
        rv = self.fixture.apply("""
           resources:
               - Checkout:
                   scm: subversion
                   name: /dest
                   repository: /source
                   branch: trunk
           """)
        self.assertEqual(MissingDependency.returncode, rv)

