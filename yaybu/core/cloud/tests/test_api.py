
import unittest
from mock import MagicMock as Mock

from yaybu.core.cloud import api

api.get_compute_driver = Mock()
api.get_storage_driver = Mock()

compute_driver = api.get_compute_driver()
storage_driver = api.get_storage_driver()

mock_image = Mock()
mock_image.id = "image"

mock_size = Mock()
mock_size.id = "size"

compute_driver.list_images = Mock(return_value=[mock_image])
compute_driver.list_sizes = Mock(return_value=[mock_size])

class TestCloud(unittest.TestCase):
    
    def _make_cloud(self):
        c = api.Cloud("compute", "storage", {})
        c.compute_class = Mock()
        c.storage_class = Mock()
        return c
    
    def test_create_node_happy(self):
        """ Test the happy path """
        c = self._make_cloud()
        c.create_node("name", "image", "size", "keypair")
        
        
        