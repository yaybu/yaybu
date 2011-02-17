from yaybutest.utils import TestCase

class TestFile(TestCase):

    def test_create_file(self):
        self.apply("""
            resources:
              - File:
                  name: /etc/somefile
                  owner: root
                  group: root
            """)

        self.failUnlessExists("/etc/somefile")
