# Copyright 2013 Isotoma Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from yaybu import error
from yaybu.tests.base import TestCase
from yaybu.tests.mocks.libcloud_storage import MockStorageDriver, MockStorageDriverArgless


class TestStaticContainer(TestCase):

    def setUp(self):
        MockStorageDriver.install(self)
        self.driver = MockStorageDriver("", "")
        self.source = self.driver.create_container("source")

    def test_invalid_source_id(self):
        self.assertRaises(error.ValueError, self.up, """
            new StaticContainer as mystorage:
                source:
                    id: DUMMYY
                    api_key: dummykey
                    secret: dummysecret
                    container: source

                destination:
                    id: DUMMY
                    api_key: dummykey
                    secret: dummysecret
                    container: destination
            """)

    def test_invalid_destination_id(self):
        self.assertRaises(error.ValueError, self.up, """
            new StaticContainer as mystorage:
                source:
                    id: DUMMY
                    api_key: dummykey
                    secret: dummysecret
                    container: source

                destination:
                    id: DUMMYY
                    api_key: dummykey
                    secret: dummysecret
                    container: destination
            """)

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

    def test_upload_file(self):
        self.source.upload_object_via_stream([], "foo")

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

        c = self.driver.get_container("destination")
        self.assertEqual(len(c.list_objects()), 2)
        self.assertEqual((c.get_object("foo").as_stream()), [])

    def test_delete_file(self):
        d = self.driver.create_container("destination")
        d.upload_object_via_stream([], "foo")
        d.get_object("foo")

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

        self.assertEqual(len(d.list_objects()), 1)
        d.get_object(".yaybu-manifest")
        self.assertRaises(Exception, d.get_object, "foo")

    def test_change_file(self):
        self.source.upload_object_via_stream(["foo"], "foo")

        d = self.driver.create_container("destination")
        d.upload_object_via_stream(["bar"], "foo")

        self.assertEqual(list(d.get_object("foo").as_stream()), ["bar"])

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

        self.assertEqual(list(d.get_object("foo").as_stream()), ["foo"])


class TestStaticContainerArgless(TestCase):

    def setUp(self):
        MockStorageDriverArgless.install(self)
        self.driver = MockStorageDriverArgless()
        self.driver.create_container("source")

    def test_empty_source(self):
        self.assertEqual(len(self.driver.list_containers()), 1)

        self.up("""
            new StaticContainer as mystorage:
                source:
                    id: DUMMY
                    container: source

                destination:
                    id: DUMMY
                    container: destination
            """)

        self.assertEqual(len(self.driver.list_containers()), 2)
