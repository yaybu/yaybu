from yaybu.provisioner.tests.fixture import TestCase
from time import sleep

class TestPackageInstallation(TestCase):

    def test_already_installed(self):
        rv = self.chroot.apply("""
            resources:
              - Package:
                  name: python
            """)
        self.assertEqual(rv, 254)

    def test_installation(self):
        self.chroot.check_apply("""
            resources:
              - Package:
                  name: hello
            """)

    def test_nonexistent_package(self):
        """ Try to install a package that does not exist. """
        rv = self.chroot.apply("""
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

        self.chroot.check_apply(hello_install)
        self.chroot.check_apply(hello_remove)
        self.chroot.check_apply(hello_install)


class TestPackageRemoval(TestCase):

    def test_installed(self):
        """ Try removing a package that is installed. """
        self.chroot.check_apply("""
            resources:
              - Package:
                  name: zip
            """)
        self.chroot.check_apply("""
            resources:
              - Package:
                  name: zip
                  policy: uninstall
            """)


