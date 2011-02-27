from yaybutest.utils import TestCase

class TestPackageInstallation(TestCase):

    def test_already_installed(self):
        self.check_apply("""
            resources:
              - Package:
                  name: python
            """)

    def test_installation(self):
        self.check_apply("""
            resources:
              - Package:
                  name: vim-tiny
            """)

