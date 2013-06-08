import os
import sys
from yaybu.provisioner.tests.harness import FakeChrootTestCase
from yaybu.core import error


class TestWatched(FakeChrootTestCase):

    def test_execute(self):
        self.fixture.check_apply("""
            hello: world

            resources:
                - Execute:
                    name: test_watched
                    command: /bin/touch {{hello}}
                    creates: /world
            """)

        self.failUnlessExists("/world")

