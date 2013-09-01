
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

