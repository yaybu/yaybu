# coding=utf-8

import unittest
import datetime
from yaybu.core import argument
from yaybu.core import resource
from yay.ast import bind


class TestArguments(unittest.TestCase):

    def test_octal(self):
        class R_test_octal(resource.Resource):
            a = argument.Octal()
            b = argument.Octal()
        r = R_test_octal(bind(dict(name="test", a="666", b=666)))
        self.assertEqual(r.a, 438)
        self.assertEqual(r.b, 438)

    def test_string(self):
        class R_test_string(resource.Resource):
            a = argument.String()
        r = R_test_string(bind(dict(name="test", a="foo")))
        self.assertEqual(r.a, "foo")
        r = R_test_string(bind(dict(name="test", a=u"foo")))
        self.assertEqual(r.a, "foo")
        r = R_test_string(bind(dict(name="test", a=u"£40")))
        self.assertEqual(r.a, u"£40")
        #r = R_test_string(bind(dict(name="test", a=u"£40".encode("utf-8"))))
        #self.assertEqual(r.a, u"£40")

    def test_integer(self):
        class R_test_integer(resource.Resource):
            a = argument.Integer()
        r = R_test_integer(bind(dict(name="test", a=10)))
        self.assertEqual(r.a, 10)
        r = R_test_integer(bind(dict(name="test", a="10")))
        self.assertEqual(r.a, 10)
        r = R_test_integer(bind(dict(name="test", a=10.5)))
        self.assertEqual(r.a, 10)

    def test_datetime(self):
        class R_test_datetime(resource.Resource):
            a = argument.DateTime()
        r = R_test_datetime(bind(dict(name="test", a="2011-02-20")))
        self.assertEqual(r.a, datetime.datetime(2011, 02, 20))

