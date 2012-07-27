
import unittest
from mock import MagicMock as Mock
from libcloud.common.types import LibcloudError

from yaybu.core.cloud import api

api.ComputeProvider = Mock()
api.StorageProvider = Mock()
api.DNSDriver = Mock()

StorageDriver = Mock()
ComputeDriver = Mock()
DNSDriver = Mock()

api.get_compute_driver = lambda x: Mock(return_value=ComputeDriver)
api.get_storage_driver = lambda x: Mock(return_value=StorageDriver)
api.get_dns_driver = lambda x: Mock(return_value=DNSDriver)

mock_image = Mock(id="image")
mock_size = Mock(id="size")

ComputeDriver.list_images = Mock(return_value=[mock_image])
ComputeDriver.list_sizes = Mock(return_value=[mock_size])

class TestCloud(unittest.TestCase):
    
    def _make_cloud(self):
        c = api.Cloud("compute", "storage", "dns", {})
        c.compute_class = Mock()
        c.storage_class = Mock()
        c.dns_class = Mock()
        return c
    
    def test_create_node_happy(self):
        """ Test the happy path """
        ComputeDriver._wait_until_running = Mock()
        mock_node = Mock()
        mock_node.name = "name"
        ComputeDriver.list_nodes = Mock(return_value=[mock_node])
        c = self._make_cloud()
        node = c.create_node("name", "image", "size", "keypair")
        self.assertEqual(node, mock_node)
        
    def test_create_node_never_starts(self):
        ComputeDriver._wait_until_running = Mock()
        ComputeDriver._wait_until_running.side_effect = LibcloudError("Boom")
        c = self._make_cloud()
        self.assertRaises(IOError, c.create_node, "name", "image", "size", "keypair")
        
    def test_create_node_naming_fail(self):
        ComputeDriver._wait_until_running = Mock()
        mock_node = Mock()
        mock_node.name = "fred"
        ComputeDriver.list_nodes = Mock(return_value=[mock_node])
        c = self._make_cloud()
        self.assertRaises(IOError, c.create_node, "name", "image", "size", "keypair")
        
        
        
        
        
        
        
        