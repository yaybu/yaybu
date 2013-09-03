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


class TestArgumentParser(TestCase):

    def test_invalid_param(self):
        self.assertRaises(error.ParseError, self.chroot.apply, """
            resources:
                - Execute:
                    name: test_invalid_param
                    commandz: /bin/touch
            """)

    def test_missing_arg(self):
        self.assertRaises(error.NoMatching, self.chroot.apply, """
            resources:
                - Execute:
                    name: test_missing_arg
                    command: /bin/touch {{hello}}
            """)

    def test_incorrect_policy(self):
        self.assertRaises(error.ParseError, self.chroot.apply, """
            resources:
                - Execute:
                    name: test_incorrect_policy
                    command: /bin/true
                    policy: executey
            """)

    def test_incorrect_policy_collection(self):
        self.assertRaises(error.ParseError, self.chroot.apply, """
            resources:
                - File:
                    name: /tmp/wibble

                - Execute:
                    name: test_incorrect_policy
                    command: /bin/true
                    policy:
                      executey:
                        - when: apply
                          on: File[/tmp/wibble]
            """)

    def test_incorrect_policy_collection_type(self):
        self.assertRaises(error.ParseError, self.chroot.apply, """
            resources:
                - File:
                    name: /tmp/wibble

                - Execute:
                    name: test_incorrect_policy
                    command: /bin/true
                    policy:
                      - execute:
                         - when: apply
                           on: File[/tmp/wibble]
            """)

    def test_incorrect_policy_collection_bind(self):
        self.assertRaises(error.BindingError, self.chroot.apply, """
            resources:
                - File:
                    name: /tmp/wibble

                - Execute:
                    name: test_incorrect_policy
                    command: /bin/true
                    policy:
                      execute:
                        - when: appply
                          on: File[/tmp/wibble]
            """)

