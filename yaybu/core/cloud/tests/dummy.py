
from libcloud.compute.drivers.dummy import DummyNodeDriver
from libcloud.storage.drivers.dummy import DummyStorageDriver
from libcloud.dns.drivers.dummy import DummyDNSDriver


class DummyComputeDriver(DummyNodeDriver):
    pass

class DummyStorageDriver(DummyStorageDriver):
    pass

class DummyDNSDriver(DummyDNSDriver):
    pass

