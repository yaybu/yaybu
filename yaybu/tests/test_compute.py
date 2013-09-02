from yaybu.tests.base import TestCase
from yaybu.tests.mocks.libcloud_compute import MockNodeDriver


class TestClusterIntegration(TestCase):

    def setUp(self):
        MockNodeDriver.install(self)
        self.driver = MockNodeDriver("", "")

    def test_empty_compute_node(self):
        self.assertEqual(len(self.driver.list_nodes()), 0)
        self.up("""
            new Compute as myserver:
                name: hello
                driver:
                    id: DUMMY
                    api_key: dummykey
                    secret: dummysecret
                image: ubuntu
                size: big
                key: foo
            """)
        nodes = self.driver.list_nodes()
        self.assertEqual(len(nodes), 1)
        # FIXME: A better mock is required before we can test the config was deployed correctly :-(
        self.assertEqual(nodes[0].name, "dummy-1")

