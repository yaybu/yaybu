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
import testtools


class TestCase(testtools.TestCase):

    def useFixture(self, fixture):
        """ Use a fixture in a test case.

        The fixture will be setUp, and self.addCleanup(fixture.cleanUp) called.

        The fixture will be available as self.fixture.

        :param fixture: The fixture to use
        :return: The fixture, after setting it up and scheduling a cleanup for it
        """
        self.fixture = fixture
        return super(TestCase, self).useFixture(fixture)

    def failUnlessExists(self, path):
        if not self.fixture.exists(path):
            self.fail("Path '%s' does not exist" % path)

    def failIfExists(self, path):
        if self.fixture.exists(path):
            self.fail("Path '%s' exists" % path)

