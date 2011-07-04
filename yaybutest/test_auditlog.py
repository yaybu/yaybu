import os
import sys
from yaybutest.utils import TestCase
from yaybu.core import error

class TestAuditLog(TestCase):

    def test_auditlog_apply(self):
        self.fixture.check_apply("""
            resources:
                - File:
                    name: /test_auditlog_apply
            """)

        self.failUnlessExists("/var/log/yaybu.log")

    def test_auditlog_simulate(self):
        self.fixture.check_apply_simulate("""
            resources:
                - File:
                    name: /test_auditlog_simulate
            """)

        self.failIfExists("/var/log/yaybu.log")

