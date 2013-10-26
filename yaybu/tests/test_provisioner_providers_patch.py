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

from yaybu.tests.provisioner_fixture import TestCase
from yaybu.core import error
import os


def sibpath(filename):
    return os.path.join(os.path.dirname(__file__), filename)


class TestPatchApply(TestCase):

    def test_create_missing_component(self):
        self.assertRaises(error.PathComponentMissing, self.apply, """
            resources:
              - Patch:
                  name: /etc/missing/filename
                  source: package://yaybu.tests/assets/empty_file
                  patch: package://yaybu.tests/assets/empty_file.diff
            """)

    def test_patch_file(self):
        self.check_apply("""
            resources:
              - Patch:
                  name: /etc/somefile
                  source: package://yaybu.tests/assets/empty_file
                  patch: package://yaybu.tests/assets/empty_file.diff
                  owner: root
                  group: root
            """)
        self.failUnlessExists("/etc/somefile")

    def test_patch_file_file(self):
        self.check_apply("""
            resources:
              - Patch:
                  name: /etc/somefile
                  source: package://yaybu.tests/assets/empty_file.diff
                  patch: package://yaybu.tests/assets/empty_file.diff
                  owner: root
                  group: root
            """)
        self.failUnlessExists("/etc/somefile")
