import os
import sys
from yaybu.provisioner.tests.fixture import TestCase
from yaybu.core import error

class TestEvents(TestCase):

    def test_nochange(self):
        self.chroot.check_apply("""
            resources:
              - Directory:
                  name: /etc/wibble
            """)

        self.assertRaises(error.NothingChanged, self.chroot.apply, """
            resources:
              - Directory:
                  name: /etc/wibble

              - File:
                  name: /frob/somedir/foo
                  policy:
                     apply:
                         when: apply
                         on: Directory[/etc/wibble]
            """)

    def test_recover(self):
        self.assertRaises(error.PathComponentMissing, self.chroot.apply, """
            resources:
              - Directory:
                  name: /etc/somedir

              - Directory:
                  name: /frob/somedir

              - File:
                  name: /frob/somedir/foo
                  policy:
                     apply:
                         when: apply
                         on: Directory[/etc/somedir]
            """)

        self.chroot.check_apply("""
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
                         on: Directory[/etc/somedir]

            """,
               "--resume")

        self.failUnlessExists("/frob/somedir/foo")

