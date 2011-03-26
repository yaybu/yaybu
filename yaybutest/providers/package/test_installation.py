from yaybutest.utils import TestCase

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

    def test_installing_java(self):
        """ Try to install java. """

class TestPackageRemoval(TestCase):

    def test_not_installed(self):
        """ Try removing a package that is not installed. """

    def test_installed(self):
        """ Try removing a package that is installed. """





