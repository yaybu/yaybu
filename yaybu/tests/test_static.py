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

