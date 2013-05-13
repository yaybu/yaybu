import unittest2
import os
import tempfile
import mock
from mock import MagicMock as Mock

from libcloud.common.types import LibcloudError

from yaybu.core.command import YaybuCmd
from yaybu.parts.compute import Compute


class ComputeTester(Compute):

    def install_yaybu(self):
        pass

    def create_runner(self):
        return mock.Mock()

    def instantiate(self):
        super(ComputeTester, self).instantiate()
        self.node.extra['dns_name'] = "fooo.bar.baz.example.com"


class TestClusterIntegration(unittest2.TestCase):

    """
    Exercises the cluster via the command line interface
    """

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

    def test_empty_compute_node(self):
        self._provision("test", """
            mylb:
                create "yaybu.parts.tests.test_compute:Compute":
                    driver:
                        id: DUMMY
                        creds: dummykey
                    image: ubuntu
                    size: big
                    key: foo
            """)

