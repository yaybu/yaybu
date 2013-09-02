
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

