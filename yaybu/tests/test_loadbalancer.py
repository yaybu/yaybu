import unittest2
import os
import tempfile
import mock

from yaybu.core.command import YaybuCmd
from yaybu.loadbalancer import LoadBalancer


class TestDNSProvision(unittest2.TestCase):

    def _config(self, contents):
        f = tempfile.NamedTemporaryFile(delete=False)
        f.write(contents)
        f.close()
        path = os.path.realpath(f.name)
        self.addCleanup(os.unlink, path)
        return path

    def _provision(self, clustername, config):
        cmd = YaybuCmd()
        return cmd.onecmd("provision %s %s" % (clustername, self._config(config)))

    def test_empty_records_list(self):
        self._provision("test", """
            mylb:
                create "yaybu.parts.loadbalancer:LoadBalancer":
                    driver:
                        id: DUMMY
                        api_key: dummykey
                        api_secret: dummysecret
            """)
