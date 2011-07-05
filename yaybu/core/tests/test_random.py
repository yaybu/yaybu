
from yaybu.harness import FakeChrootTestCase

from yaybu.core import resource
from yaybu.core import argument
from yaybu.core import error

import mock

class Test_Random(FakeChrootTestCase):

    # needs more work, particularly the File argument

    def resource_args(self, resource):
        for k, v in resource.__dict__.items():
            if isinstance(v, argument.Argument):
                yield k, v.__class__

    def resource_test_valid(self, resource):
        d = {}
        for name, klass in self.resource_args(resource):
            d[name] = klass._generate_valid()
        r = resource(**d)
        shell = mock.Mock()
        ctx = mock.Mock()
        ctx.simulate = True
        ctx.shell = shell
        ctx.shell.execute = mock.Mock(return_value=(0, '', ''))
        config = mock.Mock()
        try:
            r.apply(ctx, config)
        except error.Error:
            pass

    def NOtest_random(self):
        for r in resource.ResourceType.resources.values():
            self.resource_test_valid(r)
