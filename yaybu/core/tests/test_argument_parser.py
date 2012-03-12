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

