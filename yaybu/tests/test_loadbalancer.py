
from yaybu.tests.base import TestCase
from yaybu.tests.mocks.libcloud_loadbalancer import MockLoadBalancer


class TestLoadBalancer(TestCase):

    def setUp(self):
        MockLoadBalancer.install(self)

    def test_empty_records_list(self):
        self.up("""
            new LoadBalancer as mylb:
                name: my_test_loadbalancer

                driver:
                    id: DUMMY
                    key: hello
                    secret: password

                port: 80
                protocol: http
                algorithm: random
                members: []
            """)


