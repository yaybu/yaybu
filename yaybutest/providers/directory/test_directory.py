import os
from yaybutest.utils import TestCase

class TestDirectory(TestCase):

    def test_create_directory(self):
        self.check_apply("""
            resources:
              - Directory:
                  name: /etc/somedir
                  owner: root
                  group: root
            """)
        self.failUnlessExists("/etc/somedir")
        path = self.enpathinate("/etc/somedir")
        self.failUnless(os.path.isdir(path))
