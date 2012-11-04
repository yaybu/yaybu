
import unittest
import testtools
from mock import patch, MagicMock as Mock
from libcloud.common.types import LibcloudError

from yaybu.core.cloud import api

class TestCloud(testtools.TestCase):
    
    def _make_cloud(self):
        self.mock_image = Mock(id="image")
        self.mock_size = Mock(id="size")
        self.mock_node = Mock(name="name")

        for target in ("compute", "storage", "dns"):
            p = patch.object(api.Cloud, target)
            p.start()
            self.addCleanup(p.stop)

        c = api.Cloud("compute", "storage", "dns", {})
        c.compute.list_images.return_value = [self.mock_image]
        c.compute.list_sizes.return_value = [self.mock_size]
        c.compute._wait_until_running = Mock()
        c.compute.list_nodes.return_value = [self.mock_node]
        c.compute.create_node.return_value = self.mock_node

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

 
