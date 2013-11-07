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

from yay import errors
from yaybu import error
from yaybu.tests.base import TestCase
from yaybu.tests.mocks.libcloud_compute import MockNodeDriver, MockNodeDriverArgless


class TestCompute(TestCase):

    def setUp(self):
        MockNodeDriver.install(self)
        self.driver = MockNodeDriver("", "")

    def test_validate_driver_id(self):
        self.assertRaises(error.ValueError, self.up, """
            new Compute as myserver:
                name: hello
                driver:
                    id: DUMMYY
                    api_key: dummykey
                    secret: dummysecret
                image: 1
                size: 2
                key: foo
            """)

    def test_passing_int_to_driver(self):
        self.up("""
            new Compute as myserver:
                name: hello
                driver:
                    id: DUMMY
                    api_key: dummykey
                    secret: dummysecret
                    a: 55
                image: 1
                size: 2
                key: foo
            """)

    def test_passing_int_to_driver_exception(self):
        self.assertRaises(errors.TypeError, self.up, """
            new Compute as myserver:
                name: hello
                driver:
                    id: DUMMY
                    api_key: dummykey
                    secret: dummysecret
                    a: penguin
                image: 1
                size: 2
                key: foo
            """)

    def test_passing_str_to_driver(self):
        self.up("""
            new Compute as myserver:
                name: hello
                driver:
                    id: DUMMY
                    api_key: dummykey
                    secret: dummysecret
                    b: penguin
                image: 1
                size: 2
                key: foo
            """)

    def test_passing_str_to_driver_exception(self):
        self.assertRaises(errors.TypeError, self.up, """
            new Compute as myserver:
                name: hello
                driver:
                    id: DUMMY
                    api_key: dummykey
                    secret: dummysecret
                    b: []
                image: 1
                size: 2
                key: foo
            """)

    def test_empty_compute_node(self):
        self.assertEqual(len(self.driver.list_nodes()), 0)
        self.up("""
            new Compute as myserver:
                name: hello
                driver:
                    id: DUMMY
                    api_key: dummykey
                    secret: dummysecret
                image: 1
                size: 2
                key: foo
            """)
        nodes = self.driver.list_nodes()
        self.assertEqual(len(nodes), 1)
        self.assertEqual(nodes[0].name, "hello")

    def test_no_image(self):
        self.assertRaises(error.NoMatching, self.up, """
            new Compute as myserver:
                name: hello
                driver:
                    id: DUMMY
                    api_key: dummykey
                    secret: dummysecret
                size: 2
                key: foo
            """)

    def test_invalid_image(self):
        self.assertRaises(error.ValueError, self.up, """
            new Compute as myserver:
                name: hello
                driver:
                    id: DUMMY
                    api_key: dummykey
                    secret: dummysecret
                image: 58
                size: 2
                key: foo
            """)

    def test_no_size(self):
        self.assertRaises(error.NoMatching, self.up, """
            new Compute as myserver:
                name: hello
                driver:
                    id: DUMMY
                    api_key: dummykey
                    secret: dummysecret
                image: 1
                key: foo
            """)

    def test_invalid_size(self):
        self.assertRaises(error.ValueError, self.up, """
            new Compute as myserver:
                name: hello
                driver:
                    id: DUMMY
                    api_key: dummykey
                    secret: dummysecret
                image: 1
                size: 85
                key: foo
            """)

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
                size: 1
                key: 2
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
                image: 1
                size: 2
                key: foo
            """)
        nodes = self.driver.list_nodes()
        self.assertEqual(len(nodes), 3)
        nodes = filter(
            lambda n: n.name == "hello-im-another-node", self.driver.list_nodes())
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
                image: 1
                size: 2
                key: foo
            """)
        self.assertEqual(len(self.driver.list_nodes()), 0)


class TestComputeCluster(TestCase):

    def setUp(self):
        MockNodeDriver.install(self)
        self.driver = MockNodeDriver("", "")

    def test_compute_nodes(self):
        self.assertEqual(len(self.driver.list_nodes()), 0)
        self.up("""
            container1:
                new Compute as server:
                    name: hello1
                    driver:
                        id: DUMMY
                        api_key: dummykey
                        secret: dummysecret
                    image: 1
                    size: 2
                    key: foo

                resources:
                   - File:
                       name: /etc/hearbeat.conf
                       template_args:
                           ip: {{ container2.server.public_ip }}

            container2:
                new Compute as server:
                    name: hello2
                    driver:
                        id: DUMMY
                        api_key: dummykey
                        secret: dummysecret
                    image: 1
                    size: 2
                    key: foo

                resources:
                   - File:
                       name: /etc/hearbeat.conf
                       template_args:
                           ip: {{ container1.server.public_ip }}
            """)
        nodes = self.driver.list_nodes()
        self.assertEqual(len(nodes), 2)
        self.assertEqual(set(n.name for n in nodes), set(("hello1", "hello2")))


class TestComputeArgless(TestCase):

    def setUp(self):
        MockNodeDriverArgless.install(self)
        self.driver = MockNodeDriverArgless()

    def test_empty_compute_node(self):
        self.assertEqual(len(self.driver.list_nodes()), 0)
        self.up("""
            new Compute as myserver:
                name: hello
                driver: DUMMY
                image: 1
                size: 2
                key: foo
            """)
        nodes = self.driver.list_nodes()
        self.assertEqual(len(nodes), 1)
        self.assertEqual(nodes[0].name, "hello")
