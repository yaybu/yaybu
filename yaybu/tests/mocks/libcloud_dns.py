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

from libcloud.dns.drivers.dummy import DummyDNSDriver
from yaybu.dns import Zone


class MockDNSDriver(DummyDNSDriver):

    # The only change we make to the upstream Dummy driver is to make the state
    # persist between class invocations

    # This allows us to simulate multiple 'yaybu up' invocations with minimal
    # monkey-patching

    _zones = {}

    def __init__(self, api_key, secret):
        pass

    @classmethod
    def install(self, test_case):
        Zone.extra_drivers['DUMMY'] = MockDNSDriver
        test_case.addCleanup(Zone.extra_drivers.pop, 'DUMMY', None)
        test_case.addCleanup(setattr, MockDNSDriver, "_zones", {})

