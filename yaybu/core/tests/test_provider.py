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
        r = R(ensure=["p1"])
        self.assertRaises(resource.NonConformingPolicy, r.validate)
        r = R(ensure=["p1", "p2"], foo="a", bar="b")
        self.assertEqual(r.validate(), Prov1)
        r = R(ensure=["p1", "p3"], foo="a", bar="b")
        self.assertRaises(resource.TooManyProviders, r.validate)