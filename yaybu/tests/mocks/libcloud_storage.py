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

from libcloud.storage.drivers.dummy import DummyStorageDriver
from yaybu.static import StaticContainer


class MockStorageDriver(DummyStorageDriver):

    # We change we make to the upstream Dummy driver is to make the state
    # persist between class invocations

    # This allows us to simulate multiple 'yaybu up' invocations with minimal
    # monkey-patching

    # In addtion, we patch a few gaps in the upstream dummy driver...

    _containers = {}

    def __init__(self, api_key, secret):
        pass

    def iterate_container_objects(self, container):
        for obj in self._containers[container.name]['objects'].values():
            yield obj

    def upload_object_via_stream(self, iterator, container, object_name, extra=None):
        blocks = [block for block in iterator]
        size = sum(len(block) for block in blocks)
        o = self._add_object(container=container, object_name=object_name, size=size, extra=extra)
        o.blocks = blocks
        return o

    def download_object_as_stream(self, obj, chunk_size=None):
        return obj.blocks

    @classmethod
    def install(self, test_case):
        StaticContainer.extra_drivers['DUMMY'] = MockStorageDriver
        test_case.addCleanup(StaticContainer.extra_drivers.pop, 'DUMMY', None)
        test_case.addCleanup(setattr, MockStorageDriver, "_containers", {})

