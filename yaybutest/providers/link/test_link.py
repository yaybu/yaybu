
import os
from yaybutest.utils import TestCase


class TestLink(TestCase):

    def test_create_link(self):
        self.apply("""
            resources:
              - Link:
                  name: /etc/somelink
                  to: /etc
                  owner: root
                  group: root
            """)

        self.failUnlessExists("/etc/somelink")

    def test_remove_link(self):
        os.system("ln -s / %s" % self.enpathinate("/etc/toremovelink"))
        self.apply("""
            resources:
              - Link:
                  name: /etc/toremovelink
                  policy: remove
            """)
        self.failUnless(not os.path.exists(self.enpathinate("/etc/toremovelink")))


