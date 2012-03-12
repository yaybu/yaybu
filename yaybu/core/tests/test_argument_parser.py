import os
import sys
from yaybu.harness import FakeChrootTestCase
from yaybu.core import error


class TestArgumentParser(FakeChrootTestCase):

    def test_execute(self):
        rv = self.fixture.apply("""
            resources:
                - Execute:
                    name: test_watched
                    commandz: /bin/touch
            """)

        self.failUnlessEqual(rv, error.ParseError.returncode)

