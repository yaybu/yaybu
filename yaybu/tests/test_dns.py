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

    def test_add_records(self):
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

