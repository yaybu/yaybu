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


class TestCloud(unittest2.TestCase):
    
    def _make_cloud(self):
        self.mock_image = Mock(id="image")
        self.mock_size = Mock(id="size")
        self.mock_node = Mock(name="name")

        p = mock.patch.object(Compute, "driver")
        p.start()
        self.addCleanup(p.stop)

        Compute.driver.list_images.return_value = [self.mock_image]
        Compute.driver.list_sizes.return_value = [self.mock_size]
        Compute.driver._wait_until_running = Mock()
        Compute.driver.list_nodes.return_value = [self.mock_node]
        Compute.driver.create_node.return_value = self.mock_node

        return c
    
    def test_create_node_happy(self):
        """ Test the happy path """
        c = self._make_cloud()
        node = c.create_node("name", "image", "size", "keypair")
        self.assertEqual(node, self.mock_node)
        
    def test_create_node_never_starts(self):
        c = self._make_cloud()
        c.compute._wait_until_running.side_effect = LibcloudError("Boom")
        self.assertRaises(IOError, c.create_node, "name", "image", "size", "keypair")


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

