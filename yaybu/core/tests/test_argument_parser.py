import os
import sys
from yaybu.provisioner.tests.fixture import TestCase
from yaybu.core import error

class TestArgumentParser(TestCase):

    def test_invalid_param(self):
        self.assertRaises(error.ParseError, self.chroot.apply, """
            resources:
                - Execute:
                    name: test_invalid_param
                    commandz: /bin/touch
            """)

    def test_missing_arg(self):
        self.assertRaises(error.ParseError, self.chroot.apply, """
            resources:
                - Execute:
                    name: test_missing_arg
                    command: /bin/touch {{hello}}
            """)

    def test_incorrect_policy(self):
        self.assertRaises(error.ParseError, self.chroot.apply, """
            resources:
                - Execute:
                    name: test_incorrect_policy
                    command: /bin/true
                    policy: executey
            """)

    def test_incorrect_policy_collection(self):
        self.assertRaises(error.ParseError, self.chroot.apply, """
            resources:
                - File:
                    name: /tmp/wibble

                - Execute:
                    name: test_incorrect_policy
                    command: /bin/true
                    policy:
                      executey:
                        - when: apply
                          on: File[/tmp/wibble]
            """)

    def test_incorrect_policy_collection_type(self):
        self.assertRaises(error.ParseError, self.chroot.apply, """
            resources:
                - File:
                    name: /tmp/wibble

                - Execute:
                    name: test_incorrect_policy
                    command: /bin/true
                    policy:
                      - execute:
                         - when: apply
                           on: File[/tmp/wibble]
            """)

    def test_incorrect_policy_collection_bind(self):
        self.assertRaises(error.BindingError, self.chroot.apply, """
            resources:
                - File:
                    name: /tmp/wibble

                - Execute:
                    name: test_incorrect_policy
                    command: /bin/true
                    policy:
                      execute:
                        - when: appply
                          on: File[/tmp/wibble]
            """)

