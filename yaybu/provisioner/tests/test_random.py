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

from yaybu.provisioner.tests.fixture import TestCase

from yaybu.provisioner import resource
from yaybu.core import argument
from yaybu.core import error

import mock

"""
class Test_Random(TestCase):

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
        transport = mock.Mock()
        ctx = mock.Mock()
        ctx.simulate = True
        ctx.transport = transport
        ctx.transport.execute = mock.Mock(return_value=(0, '', ''))
        config = mock.Mock()
        try:
            r.apply(ctx, config)
        except error.Error:
            pass

    def NOtest_random(self):
        for r in resource.ResourceType.resources.values():
            self.resource_test_valid(r)
"""

