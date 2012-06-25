
import wingdbstub
import unittest
from mock import MagicMock as Mock

from yaybu.core.cloud import api

api.ComputeProvider = Mock()
api.StorageProvider = Mock()

StorageDriver = Mock()
ComputeDriver = Mock()

api.get_compute_driver = lambda x: Mock(return_value=ComputeDriver)
api.get_storage_driver = lambda x: Mock(return_value=StorageDriver)

mock_image = Mock(id="image")
mock_size = Mock(id="size")

ComputeDriver.list_images = Mock(return_value=[mock_image])
ComputeDriver.list_sizes = Mock(return_value=[mock_size])

class TestCloud(unittest.TestCase):
    
    def _make_cloud(self):
        c = api.Cloud("compute", "storage", {})
        c.compute_class = Mock()
        c.storage_class = Mock()
        return c
    
    def test_create_node_happy(self):
        """ Test the happy path """
        c = self._make_cloud()
        c.compute._wait_until_running = Mock()
        mock_node = Mock()
        mock_node.name = "name"
        ComputeDriver.list_nodes = Mock(return_value=[mock_node])
        node = c.create_node("name", "image", "size", "keypair")
        self.assertEqual(node, mock_node)
        
        
        