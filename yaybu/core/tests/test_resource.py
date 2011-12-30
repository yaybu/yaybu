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
from yaybu.core import (resource,
                        argument,
                        policy,
                        error,
                        provider,
                        change,
                        )

from mock import Mock

class F(resource.Resource):
    foo = argument.String(default="42")
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
            'name': 'test',
            'foo': u'42',
            'bar': u'20100501',
            })
        self.assertEqual(h.foo, 42)
        self.assertEqual(h.bar, datetime.datetime(2010, 05, 01))


class TestArgument(unittest.TestCase):

    def test_storage(self):
        f1 = F(name="test")
        f2 = F(name="test")
        g1 = G(name="test")
        g2 = G(name="test")
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
        f = F(name="test")
        self.assertEqual(f.foo, "42")

    def test_integer(self):
        h = H(name="test")
        h.foo = u"42"
        self.assertEqual(h.foo, 42)

    def test_datetime(self):
        h = H(name="test")
        h.bar = "20100105"
        self.assertEqual(h.bar, datetime.datetime(2010, 1, 5))


class TestArgumentAssertion(unittest.TestCase):

    def test_present(self):
        class P(policy.Policy):
            signature = [policy.Present("foo")]
        class Q(policy.Policy):
            signature = [policy.Present("bar")]
        class R(policy.Policy):
            signature = [policy.Present("baz")]
        f = F(name="test")
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
        f = F(name="test")
        self.assertEqual(P.conforms(f), False)
        self.assertEqual(Q.conforms(f), True)
        self.assertRaises(AttributeError, R.conforms, f)

    def test_and(self):
        class P(policy.Policy):
            signature = [policy.Present("foo"),
                         policy.Absent("bar"),
                         ]
        f = F(name="test")
        self.assertEqual(P.conforms(f), True)

    def test_xor(self):
        class P(policy.Policy):
            signature = [policy.XOR(
                              policy.Present("foo"),
                              policy.Present("bar"),
                         )]
        g = G(name="test")
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
    name = "foo"
    resource = Ev1

class Ev1BarPolicy(policy.Policy):
    name = "bar"
    resource = Ev1

class Ev1BazPolicy(policy.Policy):
    name = "baz"
    resource = Ev1

class Ev1Provider(provider.Provider):
    policies = (Ev1FooPolicy, Ev1BarPolicy, Ev1BazPolicy)

    applied = 0

    def apply(self, shell):
        Ev1Provider.applied += 1
        return True

class TestResourceBundle(unittest.TestCase):

    def setUp(self):
        from yaybu.core import event
        event.reset()

    def test_creation(self):
        resources = resource.ResourceBundle.create_from_list([
            {"File": [{
                "name": "/etc/foo",
                "mode": "666",
                }]
             }])
        self.assertEqual(resources["File[/etc/foo]"].mode, 438)

    def test_firing(self):
        Ev1Provider.applied = 0
        resources = resource.ResourceBundle.create_from_list([
            {"Ev1": [
                { "name": "e1",
                  "policy": "foo",
                }, {
                  "name": "e2",
                  "policy":
                      {"baz": [{
                          "when": "foo",
                          "on": "Ev1[e1]",
                          }],
                       },
                  },
            ]}])

        e1 = resources['Ev1[e1]']
        e2 = resources['Ev1[e2]']
        resources.bind()
        self.assertEqual(dict(e2.observers), {})
        self.assertEqual(dict(e1.observers),
                         {'foo': [
                             (True, e2, 'baz')]
                          })
        shell = Mock()
        p1 = e1.get_default_policy().get_provider({})
        p2 = e2.get_default_policy().get_provider({})
        self.assertEqual(p1, Ev1Provider)
        self.assertEqual(p2, provider.NullProvider)
        e1.apply(shell)
        self.assertEqual(Ev1Provider.applied, 1)
        e2.apply(shell)
        self.assertEqual(Ev1Provider.applied, 2)

    def test_not_firing(self):
        Ev1Provider.applied = 0
        resources = resource.ResourceBundle.create_from_list([
            {"Ev1": [
                { "name": "e1",
                  "policy": "foo",
                }, {
                  "name": "e2",
                  "policy":
                      {"baz": [{
                          "when": "baz",
                          "on": "Ev1[e1]",
                          }],
                       },
                  },
            ]}])
        e1 = resources['Ev1[e1]']
        e2 = resources['Ev1[e2]']
        resources.bind()
        self.assertEqual(dict(e2.observers), {})
        self.assertEqual(dict(e1.observers),
                         {'baz': [
                             (True, e2, 'baz')]
                          })
        shell = Mock()
        p1 = e1.get_default_policy().get_provider({})
        p2 = e2.get_default_policy().get_provider({})
        self.assertEqual(p1, Ev1Provider)
        self.assertEqual(p2, provider.NullProvider)
        e1.apply(shell)
        self.assertEqual(Ev1Provider.applied, 1)
        e2.apply(shell)
        self.assertEqual(Ev1Provider.applied, 1)

    def test_forwardreference(self):
        Ev1Provider.applied = 0
        resources = resource.ResourceBundle.create_from_list([
            {"Ev1": [
                { "name": "e1",
                  "policy":
                      {"baz": [{
                          "when": "baz",
                          "on": "Ev1[e2]",
                          }],
                       },
                }, {
                  "name": "e2",
                  "policy": "foo",
                  }
            ]}])
        e1 = resources['Ev1[e1]']
        e2 = resources['Ev1[e2]']
        self.assertRaises(error.BindingError, resources.bind)

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
        self.assertEqual(len(e1.observers), 0)
        self.assertEqual(dict(e2.observers), {
            'bar': [(True, e1, 'pol1')]
            })

    def test_multiple(self):
        e1 = Ev1(name="e1",
                policy = {
                    'pol1': [{
                        'when': 'bar',
                        'on': 'e2'}],
                    'pol2': [{
                        'when': 'foo',
                        'on': 'e3'}],
                    'pol3': [{
                        'when': 'baz',
                        'on': 'e2',
                        }]
                    })
        e2 = Ev1(name="e2")
        e3 = Ev1(name="e3")
        resources = {'e1': e1, 'e2': e2, 'e3': e3}
        e1.bind(resources)
        e2.bind(resources)
        self.assertEqual(dict(e1.observers), {})
        self.assertEqual(dict(e2.observers), {
            'bar': [(True, e1, 'pol1')],
            'baz': [(True, e1, 'pol3')],
            })
        self.assertEqual(dict(e3.observers), {
            'foo': [(True, e1, 'pol2')],
            })

    def test_missing(self):
        e1 = Ev1(name="e1",
                policy = {
                    'pol1': [{
                        'when': 'bar',
                        'on': 'missing'}],
                    })
        e2 = Ev1(name="e2")
        resources = {'e1': e1, 'e2': e2}
        self.assertRaises(error.BindingError, e1.bind, resources)
