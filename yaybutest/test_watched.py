import os
import sys
from yaybutest.utils import TestCase
from yaybu.core import error

class TestWatched(TestCase):

    def test_watched(self):
        self.check_apply("""
            resources:
                - Execute:
                    name: test_watched
                    command: touch /watched-file
                    watch:
                      - /watched-file
                - Execute:
                    name: test_output
                    command: touch /event-triggered
                    policy:
                        execute:
                            when: watched
                            on: File[/watched-file]
            """)
        self.failUnlessExists("/event-triggered")

