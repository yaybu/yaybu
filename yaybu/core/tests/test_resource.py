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

import os
import unittest
import datetime
from yaybu.core import resource
from yaybu.core import argument
from yaybu.core import policy

class F(resource.Resource):
    foo = argument.String("42")
    bar = argument.String()

class G(resource.Resource):
    foo = argument.String()
    bar = argument.String()

class H(resource.Resource):
    foo = argument.Integer()
    bar = argument.DateTime()
    baz = argument.File()

class TestResource(unittest.TestCase):

    def test_init(self):
        h = H(**{
            'foo': u'42',
            'bar': u'20100501',
            })
        self.assertEqual(h.foo, 42)
        self.assertEqual(h.bar, datetime.datetime(2010, 05, 01))


class TestArgument(unittest.TestCase):

    def test_storage(self):
        f1 = F()
        f2 = F()
        g1 = G()
        g2 = G()
        f1.foo = "a"
        f1.bar = "b"
        f2.foo = "c"
        f2.bar = "d"
        g1.foo = "e"
        g1.bar = "f"
        g2.foo = "g"
        g2.bar = "h"
        self.assertEqual(f1.foo, "a")
        self.assertEqual(f1.bar, "b")
        self.assertEqual(f2.foo, "c")
        self.assertEqual(f2.bar, "d")
        self.assertEqual(g1.foo, "e")
        self.assertEqual(g1.bar, "f")
        self.assertEqual(g2.foo, "g")
        self.assertEqual(g2.bar, "h")

    def test_default(self):
        f = F()
        self.assertEqual(f.foo, "42")

    def test_integer(self):
        h = H()
        h.foo = u"42"
        self.assertEqual(h.foo, 42)

    def test_datetime(self):
        h = H()
        h.bar = "20100105"
        self.assertEqual(h.bar, datetime.datetime(2010, 1, 5))

    def test_package_file(self):
        h = H()
        h.baz = "package://yaybu.core/tests/example.txt"
        self.assertEqual(h.baz, os.path.join(os.path.dirname(__file__), "example.txt"))

    def test_recipe_file(self):
        h = H()
        h.baz = "recipe://yaybu.distro/interfaces.j2"
        self.assertEqual(h.baz,
                         os.path.join(
                             os.path.dirname(
                                 os.path.dirname(
                                     os.path.dirname(__file__)
                                 )
                            )
                        , "recipe/interfaces.j2"))

class TestArgumentAssertion(unittest.TestCase):

    def test_present(self):
        class P(policy.Policy):
            signature = [policy.Present("foo")]
        class Q(policy.Policy):
            signature = [policy.Present("bar")]
        class R(policy.Policy):
            signature = [policy.Present("baz")]
        f = F()
        self.assertEqual(P.conforms(f), True)
        self.assertEqual(Q.conforms(f), False)
        self.assertRaises(AttributeError, R.conforms, f)

    def test_absent(self):
        class P(policy.Policy):
            signature = [policy.Absent("foo")]
        class Q(policy.Policy):
            signature = [policy.Absent("bar")]
        class R(policy.Policy):
            signature = [policy.Absent("baz")]
        f = F()
        self.assertEqual(P.conforms(f), False)
        self.assertEqual(Q.conforms(f), True)
        self.assertRaises(AttributeError, R.conforms, f)

    def test_and(self):
        class P(policy.Policy):
            signature = [policy.Present("foo"),
                         policy.Absent("bar"),
                         ]
        f = F()
        self.assertEqual(P.conforms(f), True)

    def test_xor(self):
        class P(policy.Policy):
            signature = [policy.XOR(
                              policy.Present("foo"),
                              policy.Present("bar"),
                         )]
        g = G()
        self.assertEqual(P.conforms(g), False)
        g.foo = "yes"
        self.assertEqual(P.conforms(g), True)
        g.bar = "yes"
        self.assertEqual(P.conforms(g), False)
        g.foo = None
        self.assertEqual(P.conforms(g), True)


class Ev1(resource.Resource):
    pass

class Ev1FooPolicy(policy.Policy):
    pass

class Ev1BarPolicy(policy.Policy):
    pass

class Ev1BazPolicy(policy.Policy):
    pass

class PolicyBindingTests(unittest.TestCase):
    def test_structure(self):
        e1 = Ev1(name="e1",
                policy = {
                    'pol1': {
                        'when': 'bar',
                        'on': 'e2'},
                    })
        e2 = Ev1(name="e2")
        resources = {'e1': e1, 'e2': e2}
        e1.bind(resources)
        e2.bind(resources)
        self.assertEqual(e2.observers['bar'],
                         [(True, e1, 'pol1')])
