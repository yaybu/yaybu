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

# (This is to test that resources we define outsite of yaybu.resources can
# be picked up by whitehat)
from yaybu.core import resource
class WhiteHat(resource.Resource):
    pass

import unittest
from yaybu.core.whitehat import *


def dummy_function(sitename):
    Directory(
        name = '{sitename}',
        )


class TestWhitehat(unittest.TestCase):

    def setUp(self):
        reset_bundle()

    def at(self, idx):
        return get_bundle().values()[idx]

    def test_custom_resources(self):
        WhiteHat(name='hello')
        self.failUnlessEqual(self.at(0).name, 'hello')

    def test_simple_locals(self):
        local1 = 'hello'
        local2 = '0755'

        File(
            name = '/etc/{local1}',
            mode = '{local2}',
            )

    def test_for_each(self):
        for i in range(3):
            Service(
                name = 'zope{i}',
                )

        self.failUnlessEqual(self.at(0).name, 'zope0')
        self.failUnlessEqual(self.at(1).name, 'zope1')
        self.failUnlessEqual(self.at(2).name, 'zope2')

    def test_function(self):
        dummy_function('/www.foo.com')
        self.failUnlessEqual(self.at(0).name, '/www.foo.com')

    def test_inner_function(self):
        def dummy_function(somevar):
            Directory(
                name = '/www.foo.com-{somevar}',
                )
        dummy_function('test')

        self.failUnlessEqual(self.at(0).name, '/www.foo.com-test')

