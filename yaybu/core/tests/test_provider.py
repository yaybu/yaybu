# Copyright 2011 Isotoma Limited
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


import unittest

from yaybu.core import resource
from yaybu.core import policy
from yaybu.core import argument
from yaybu.core import provider

class R(resource.Resource):
    foo = argument.String()
    bar = argument.String()

class P1(policy.Policy):
    default = True
    name = 'p1'
    resource = R
    signature = [policy.Present("foo")]

class P2(policy.Policy):
    name = 'p2'
    resource = R
    signature = [policy.Present("bar")]

class P3(policy.Policy):
    name = 'p3'
    resource = R
    signature = [policy.Present("foo"),
                 policy.Present("bar")]

class Prov1(provider.Provider):
    policies = [P1,P2]

class Prov2(provider.Provider):
    policies = [P3]

class TestOrchestration(unittest.TestCase):

    def test_validate(self):
        r = R(foo="a", bar="b")
        self.assertEqual(r.validate(), Prov1)
        r = R()
        self.assertRaises(resource.NonConformingPolicy, r.validate)
        r = R(policy="p1")
        self.assertRaises(resource.NonConformingPolicy, r.validate)
