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

from libcloud.loadbalancer.base import Algorithm, Member

from yaybu.tests.base import TestCase
from yaybu.tests.mocks.libcloud_loadbalancer import MockLoadBalancer


class TestLoadBalancer(TestCase):

    def setUp(self):
        MockLoadBalancer.install(self)
        self.driver = MockLoadBalancer('', '')

    def test_empty_records_list(self):
        self.assertEqual(self.driver.list_balancers(), [])

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

        balancers = self.driver.list_balancers()
        self.assertEqual(len(balancers), 1)
        self.assertEqual(balancers[0].name, "my_test_loadbalancer")
        self.assertEqual(balancers[0].port, 80)

    def test_destroy(self):
        self.test_empty_records_list()
        self.destroy("""
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
        self.assertEqual(len(self.driver.list_balancers()), 0)

    def test_add_member_to_new(self):
        self.assertEqual(self.driver.list_balancers(), [])

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

                members:
                  - id: member1
            """)
        balancers = self.driver.list_balancers()
        self.assertEqual(len(balancers), 1)

        members = balancers[0].list_members()
        self.assertEqual(len(members), 1)
        self.assertEqual(members[0].id, "member1")

    def test_add_member_to_existing(self):
        balancer = self.driver.create_balancer("my_existing_balancer", 80, "http", Algorithm.RANDOM, [])

        self.up("""
            new LoadBalancer as mylb:
                name: my_existing_balancer

                driver:
                    id: DUMMY
                    key: hello
                    secret: password

                port: 80
                protocol: http
                algorithm: random

                members:
                  - id: member1
            """)

        members = balancer.list_members()
        self.assertEqual(len(members), 1)
        self.assertEqual(members[0].id, "member1")

    def test_remove_member_from_existing(self):
        member1 = Member(id="member1", ip="127.0.0.1", port=80)
        balancer = self.driver.create_balancer("my_existing_balancer", 80, "http", Algorithm.RANDOM, [member1])

        self.up("""
            new LoadBalancer as mylb:
                name: my_existing_balancer

                driver:
                    id: DUMMY
                    key: hello
                    secret: password

                port: 80
                protocol: http
                algorithm: random

                members: []
            """)

        members = self.driver.get_balancer(balancer.id).list_members()
        self.assertEqual(len(members), 0)

