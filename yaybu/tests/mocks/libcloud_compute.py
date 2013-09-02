
from libcloud.compute.drivers.dummy import DummyNodeDriver
from yaybu.compute import Compute


class MockNodeDriver(DummyNodeDriver):

    # The only change we make to the upstream Dummy driver is to make the state
    # persist between class invocations

    # This allows us to simulate multiple 'yaybu up' invocations with minimal
    # monkey-patching

    nl = []

    def __init__(self, api_key, secret):
        pass

    @classmethod
    def install(self, test_case):
        Compute.extra_drivers['DUMMY'] = MockNodeDriver
        test_case.addCleanup(Compute.extra_drivers.pop, 'DUMMY', None)
        test_case.addCleanup(setattr, MockNodeDriver, "nl", [])

