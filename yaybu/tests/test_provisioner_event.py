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


class TestEvents(TestCase):

    def test_nochange(self):
        self.chroot.check_apply("""
            resources:
              - Directory:
                  name: /etc/wibble
            """)

        self.assertRaises(error.NothingChanged, self.chroot.apply, """
            resources:
              - Directory:
                  name: /etc/wibble

              - File:
                  name: /frob/somedir/foo
                  policy:
                     apply:
                         when: apply
                         on: Directory[/etc/wibble]
            """)

    def test_recover(self):
        self.assertRaises(error.PathComponentMissing, self.chroot.apply, """
            resources:
              - Directory:
                  name: /etc/somedir

              - Directory:
                  name: /frob/somedir

              - File:
                  name: /frob/somedir/foo
                  policy:
                     apply:
                         when: apply
                         on: Directory[/etc/somedir]
            """)

        self.chroot.check_apply("""
            resources:
              - Directory:
                  name: /etc/somedir

              - Directory:
                  name: /frob

              - Directory:
                  name: /frob/somedir

              - File:
                  name: /frob/somedir/foo
                  policy:
                     apply:
                         when: apply
                         on: Directory[/etc/somedir]

            """,
               "--resume")

        self.failUnlessExists("/frob/somedir/foo")

