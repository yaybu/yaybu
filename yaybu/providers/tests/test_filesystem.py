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
from yay import String
from yaybu.providers.filesystem import files

class TestSecretTemplateArgs(unittest.TestCase):

    def setUp(self):
        self.ps = String()
        self.ps.add_secret('hello')

        class DummyResource:
            template_args = {}

        self.args = DummyResource.template_args
        self.provider = files.File(DummyResource)

    def test_no_secret(self):
        self.args['level1'] = dict(foo=1, bar=[1,2,3], baz=dict())
        self.failUnless(not self.provider.has_protected_strings())

    def test_secret_in_dict(self):
        self.args['level1'] = dict(foo=self.ps, bar=1)
        self.failUnless(self.provider.has_protected_strings())

    def test_secret_in_list(self):
        self.args['level1'] = [self.ps, 1, 2]
        self.failUnless(self.provider.has_protected_strings())

    def test_secret_in_dict_in_list(self):
        self.args['level1'] = [dict(foo=self.ps, bar=1)]
        self.failUnless(self.provider.has_protected_strings())

