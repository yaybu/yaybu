# coding=utf-8

import unittest
import datetime
from yaybu.core import argument
from yaybu.core import resource

class TestArguments(unittest.TestCase):

    def test_octal(self):
        class R_test_octal(resource.Resource):
            a = argument.Octal()
        r = R_test_octal(name="test")
        r.a = "666"
        self.assertEqual(r.a, 438)
        r.a = 666
        self.assertEqual(r.a, 438)

    def test_string(self):
        class R_test_string(resource.Resource):
            a = argument.String()
        r = R_test_string(name="test")
        r.a = "foo"
        self.assertEqual(r.a, "foo")
        r.a = u"foo"
        self.assertEqual(r.a, "foo")
        r.a = u"£40"
        self.assertEqual(r.a, u"£40")
        r.a = u"£40".encode("utf-8")
        self.assertEqual(r.a, u"£40")

    def test_integer(self):
        class R_test_integer(resource.Resource):
            a = argument.Integer()
        r = R_test_integer(name="test")
        r.a = 10
        self.assertEqual(r.a, 10)
        r.a = "10"
        self.assertEqual(r.a, 10)
        r.a = 10.5
        self.assertEqual(r.a, 10)

    def test_datetime(self):
        class R_test_datetime(resource.Resource):
            a = argument.DateTime()
        r = R_test_datetime(name="test")
        r.a = "2011-02-20"
        self.assertEqual(r.a, datetime.datetime(2011, 02, 20))

