
from yaybu.tests.base import TestCase
from yaybu.tests.mocks.libcloud_dns import MockDNSDriver


class TestZone(TestCase):

    def setUp(self):
        MockDNSDriver.install(self)

    def test_empty_records_list(self):
        self.up("""
            new Zone as myzone:
                    driver:
                        id: DUMMY
                        api_key: dummykey
                        secret: dummysecret
                    domain: example.com
                    records: []
            """)

    def __test_add_records(self):
        self.up("""
            new Zone as myzone:
                    driver:
                        id: DUMMY
                        api_key: dummykey
                        secret: dummysecret
                    domain: example.com
                    records:
                      - name: www
                        data: 127.0.0.1
            """)

