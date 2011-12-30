from yaybu.harness import FakeChrootTestCase
from time import sleep

class TestPackageInstallation(FakeChrootTestCase):

    def test_already_installed(self):
        rv = self.fixture.apply("""
            resources:
              - Package:
                  name: python
            """)
        self.assertEqual(rv, 254)

    def test_installation(self):
        self.fixture.check_apply("""
            resources:
              - Package:
                  name: hello
            """)

    def test_nonexistent_package(self):
        """ Try to install a package that does not exist. """
        rv = self.fixture.apply("""
            resources:
              - Package:
                  name: zzzz
            """)
        self.assertEqual(rv, 132)

    def test_package_reinstallation(self):
        """ Try reinstalling a previously-removed package """
        hello_install = """
            resources:
              - Package:
                  name: hello
            """

        hello_remove = """
            resources:
              - Package:
                  name: hello
                  policy: uninstall
            """

        self.fixture.check_apply(hello_install)
        self.fixture.check_apply(hello_remove)
        self.fixture.check_apply(hello_install)


class TestPackageRemoval(FakeChrootTestCase):

    def test_installed(self):
        """ Try removing a package that is installed. """
        self.fixture.check_apply("""
            resources:
              - Package:
                  name: ubuntu-keyring
                  policy: uninstall
            """)


