import os
import sys
from yaybu.provisioner.tests.fixture import TestCase
from yaybu.core import error


class TestWatched(TestCase):

    def test_watched(self):
        self.fixture.check_apply("""
            resources:
                - Execute:
                    name: test_watched
                    command: touch /watched-file
                    creates: /watched-file
                    watch:
                      - /watched-file
                - Execute:
                    name: test_output
                    command: touch /event-triggered
                    creates: /event-triggered
                    policy:
                        execute:
                            when: watched
                            on: File[/watched-file]
            """)
        self.failUnlessExists("/event-triggered")

