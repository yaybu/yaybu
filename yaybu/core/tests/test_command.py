# coding=utf-8
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


import unittest
from yaybu.core import config
from yaybu.core.error import ArgParseError


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
        self.assertRaises(ArgParseError, arg.get)
        
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
        self.assertRaises(ArgParseError, arg.get)
        
        
        
