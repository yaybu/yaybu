
from libcloud.compute.drivers.dummy import DummyNodeDriver
from libcloud.storage.drivers.dummy import DummyStorageDriver as OrigDummyStorageDriver
from libcloud.dns.drivers.dummy import DummyDNSDriver as OrigDummyDNSDriver


class DummyComputeDriver(DummyNodeDriver):
    pass

class DummyStorageDriver(OrigDummyStorageDriver):
    
    def upload_object_via_stream(self, iterator, container, object_name, extra=None):
        """ I want to support a StringIO """
        pass

class DummyDNSDriver(OrigDummyDNSDriver):
    pass

