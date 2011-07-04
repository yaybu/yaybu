
from yaybu.harness import TestCase, FakeChrootFixture

class TestCase(TestCase):

    def setUp(self):
        super(TestCase, self).setUp()
        self.useFixture(FakeChrootFixture())

