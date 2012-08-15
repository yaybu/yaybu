import os
import sys
from yaybu.harness import FakeChrootTestCase
from yaybu.core import error

class TestArgumentParser(FakeChrootTestCase):

    def test_invalid_param(self):
        rv = self.fixture.apply("""
            resources:
                - Execute:
                    name: test_invalid_param
                    commandz: /bin/touch
            """)

        self.failUnlessEqual(rv, error.ParseError.returncode)

    def test_missing_arg(self):
        rv = self.fixture.apply("""
            resources:
                - Execute:
                    name: test_missing_arg
                    command: /bin/touch ${hello}
            """)

        self.failUnlessEqual(rv, error.ParseError.returncode)

    def test_incorrect_policy(self):
        rv = self.fixture.apply("""
            resources:
                - Execute:
                    name: test_incorrect_policy
                    command: /bin/true
                    policy: executey
            """)

        self.failUnlessEqual(rv, error.ParseError.returncode)

    def test_incorrect_policy_collection(self):
        rv = self.fixture.apply("""
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

        self.failUnlessEqual(rv, error.ParseError.returncode)

    def test_incorrect_policy_collection_type(self):
        rv = self.fixture.apply("""
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

        self.failUnlessEqual(rv, error.ParseError.returncode)

    def test_incorrect_policy_collection_bind(self):
        rv = self.fixture.apply("""
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

        self.failUnlessEqual(rv, error.BindingError.returncode)

