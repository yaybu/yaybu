import os, shutil, grp

from yaybutest.utils import TestCase
from yaybu.util import sibpath


class TestSimpleService(TestCase):

    def test_start(self):
        self.check_apply("""
            resources:
                - Service:
                    name: test
                    policy: start
                    start: touch /foo
            """)

        self.failUnlessExists("/foo")


    def test_stop(self):
        self.check_apply("""
            resources:
                - Service:
                    name: test
                    policy: stop
                    stop: touch /foo
            """)

        self.failUnlessExists("/foo")

    def test_restart(self):
        rv = self.apply("""
            resources:
                - Service:
                    name: test
                    policy: restart
                    restart: touch /foo
            """)

        # We restart every time config is applied - so check_apply would fail the
        # automatic idempotentcy check
        self.failUnlessEqual(rv, 0)
        self.failUnlessExists("/foo")
