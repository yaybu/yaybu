# coding=utf-8

import unittest
from yaybu.core import config


class TestYaybuArg(unittest.TestCase):
    
    def test_string(self):
        arg = config.YaybuArg('foo')
        arg.set("hello")
        self.assertEqual(arg.get(), "hello")
        
    def test_default(self):
        arg = config.YaybuArg('foo', default="hello")
        self.assertEqual(arg.get(), "hello")
        
    def test_integer(self):
        arg = config.YaybuArg('foo', 'integer')
        arg.set("10")
        self.assertEqual(arg.get(), 10)
        
    def test_boolean_default(self):
        arg = config.YaybuArg('foo', 'boolean', default=False)
        self.assertEqual(arg.get(), False)
        
    def test_integer_default(self):
        arg = config.YaybuArg('foo', 'integer', default=20)
        self.assertEqual(arg.get(), 20)
        
    def test_integer_bad(self):
        arg = config.YaybuArg('foo', 'integer', default=20)
        arg.set("boo")
        self.assertRaises(config.YaybuArgParsingError, arg.get)
        
    def test_boolean(self):
        arg = config.YaybuArg('foo', 'boolean')
        arg.set("1")
        self.assertEqual(arg.get(), True)
        arg.set("yes")
        self.assertEqual(arg.get(), True)
        arg.set("Yes")
        self.assertEqual(arg.get(), True)
        arg.set("True")
        self.assertEqual(arg.get(), True)
        arg.set("0")
        self.assertEqual(arg.get(), False)
        arg.set("no")
        self.assertEqual(arg.get(), False)
        arg.set("false")
        self.assertEqual(arg.get(), False)
    
    def test_unknown(self):
        arg = config.YaybuArg('foo', 'meh', default=20)
        arg.set("boo")
        self.assertRaises(config.YaybuArgParsingError, arg.get)
        
        
        
