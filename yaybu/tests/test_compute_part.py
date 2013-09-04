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
        self.assertEqual(nodes[0].name, "hello")

    def test_node_already_exists(self):
        self.assertEqual(len(self.driver.list_nodes()), 0)
        self.driver.create_node(name="dummy-1")
        self.assertRaises(error.NothingChanged, self.up, """
            new Compute as myserver:
                name: dummy-1
                driver:
                    id: DUMMY
                    api_key: dummykey
                    secret: dummysecret
                image: ubuntu
                size: big
                key: foo
            """)

    def test_another_compute_node(self):
        self.assertEqual(len(self.driver.list_nodes()), 0)
        self.driver.create_node()
        self.driver.create_node()
        self.up("""
            new Compute as myserver:
                name: hello-im-another-node
                driver:
                    id: DUMMY
                    api_key: dummykey
                    secret: dummysecret
                image: ubuntu
                size: big
                key: foo
            """)
        nodes = self.driver.list_nodes()
        self.assertEqual(len(nodes), 3)
        nodes = filter(lambda n: n.name == "hello-im-another-node", self.driver.list_nodes())
        self.assertEqual(len(nodes), 1)
        self.assertEqual(nodes[0].name, "hello-im-another-node")

    def test_destroy(self):
        self.test_empty_compute_node()
        self.destroy("""
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
        self.assertEqual(len(self.driver.list_nodes()), 0)

