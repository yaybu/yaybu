import os
import sys
from yaybutest.utils import TestCase
from yaybu.core import error
import time

class TestEvents(TestCase):

    def test_recover(self):
        rv = self.apply("""
            resources:
              - Directory:
                  name: /etc/somedir

              - Directory:
                  name: /frob

              - Directory:
                  name: /frob/somedir

              - File:
                  name: /frob/somedir/foo
                  policy:
                     apply:
                         when: apply
                         on: /etc/somedir
            """)
        #open("/tmp/events.saved", "w").write(open(self.enpathinate("/var/run/yaybu/events.saved")).read())
        #self.assertEqual(rv, error.PathComponentMissing.returncode)
        print >>sys.stderr, "XXXXX"
        self.check_apply("""
            resources:
              - Directory:
                  name: /etc/somedir

              - Directory:
                  name: /frob

              - Directory:
                  name: /frob/somedir

              - File:
                  name: /frob/somedir/foo
                  policy:
                     apply:
                         when: apply
                         on: /etc/somedir
            """)
        self.failUnlessExists("/frob/somedir/foo")
