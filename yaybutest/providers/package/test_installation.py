from yaybutest.utils import TestCase
from time import sleep

class TestPackageInstallation(TestCase):

    def test_already_installed(self):
        rv = self.apply("""
            resources:
              - Package:
                  name: python
            """)
        self.assertEqual(rv, 255)

    def test_installation(self):
        self.check_apply("""
            resources:
              - Package:
                  name: vim-tiny
            """)

    def test_nonexistent_package(self):
        """ Try to install a package that does not exist. """
        rv = self.apply("""
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

        self.check_apply(hello_install)
        sleep(5)
        self.check_apply(hello_remove)
        sleep(5)
        self.check_apply(hello_install)


class TestPackageRemoval(TestCase):

    def test_not_installed(self):
        """ Try removing a package that is not installed. """
        self.check_apply("""
            resources:
                - Package:
                    name: vim-tiny
                    policy: uninstall
            """)

    def test_installed(self):
        """ Try removing a package that is installed. """
        self.check_apply("""
            resources:
              - Package:
                  name: vim-tiny
                  policy: uninstall
            """)


