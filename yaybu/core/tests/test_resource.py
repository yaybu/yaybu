
import os
import unittest
import datetime
from yaybu.core import resource

class F(resource.Resource):
    foo = resource.String("42")
    bar = resource.String()

class G(resource.Resource):
    foo = resource.String()
    bar = resource.String()

class H(resource.Resource):
    foo = resource.Integer()
    bar = resource.DateTime()
    baz = resource.File()

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
        class P(resource.Policy):
            signature = [resource.Present("foo")]
        class Q(resource.Policy):
            signature = [resource.Present("bar")]
        class R(resource.Policy):
            signature = [resource.Present("baz")]
        f = F()
        self.assertEqual(P.conforms(f), True)
        self.assertEqual(Q.conforms(f), False)
        self.assertRaises(AttributeError, R.conforms, f)

    def test_absent(self):
        class P(resource.Policy):
            signature = [resource.Absent("foo")]
        class Q(resource.Policy):
            signature = [resource.Absent("bar")]
        class R(resource.Policy):
            signature = [resource.Absent("baz")]
        f = F()
        self.assertEqual(P.conforms(f), False)
        self.assertEqual(Q.conforms(f), True)
        self.assertRaises(AttributeError, R.conforms, f)

    def test_and(self):
        class P(resource.Policy):
            signature = [resource.Present("foo"),
                         resource.Absent("bar"),
                         ]
        f = F()
        self.assertEqual(P.conforms(f), True)

    def test_xor(self):
        class P(resource.Policy):
            signature = [resource.XOR(
                              resource.Present("foo"),
                              resource.Present("bar"),
                         )]
        g = G()
        self.assertEqual(P.conforms(g), False)
        g.foo = "yes"
        self.assertEqual(P.conforms(g), True)
        g.bar = "yes"
        self.assertEqual(P.conforms(g), False)
        g.foo = None
        self.assertEqual(P.conforms(g), True)


