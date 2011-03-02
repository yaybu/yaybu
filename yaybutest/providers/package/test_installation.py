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

