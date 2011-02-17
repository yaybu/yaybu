from yaybutests.utils import TestCase

class TestPackageInstallation(TestCase):

    def test_already_installed(self):
        self.apply("""
            resources:
              - Package:
                  name: python
            """)

    def test_installation(self):
        self.apply("""
            resources:
              - Package:
                  name: vim-tiny
            """)

