
from yaybu.tests.base import TestCase
from yaybu.tests.mocks.libcloud_storage import MockStorageDriver


class TestStaticContainer(TestCase):

    def setUp(self):
        MockStorageDriver.install(self)
        self.driver = MockStorageDriver("", "")
        self.driver.create_container("source")

    def test_empty_source(self):
        self.assertEqual(len(self.driver.list_containers()), 1)

        self.up("""
            new StaticContainer as mystorage:
                source:
                    id: DUMMY
                    api_key: dummykey
                    secret: dummysecret
                    container: source

                destination:
                    id: DUMMY
                    api_key: dummykey
                    secret: dummysecret
                    container: destination
            """)

        self.assertEqual(len(self.driver.list_containers()), 2)

