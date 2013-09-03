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
from yaybu import error

class TestPackageInstallation(TestCase):

    def test_already_installed(self):
        self.assertRaises(error.NothingChanged, self.chroot.apply, """
            resources:
              - Package:
                  name: python
            """)

    def test_installation(self):
        self.chroot.check_apply("""
            resources:
              - Package:
                  name: hello
            """)

    def test_nonexistent_package(self):
        """ Try to install a package that does not exist. """
        self.assertRaises(error.AptError, self.chroot.apply, """
            resources:
              - Package:
                  name: zzzz
            """)

    def test_package_reinstallation(self):
        """ Try reinstalling a previously-removed package """
        hello_install = """
            resources:
              - Package:
                  name: hello
            """

        hello_remove = """
            resources:
              - Package:
                  name: hello
                  policy: uninstall
            """

        self.chroot.check_apply(hello_install)
        self.chroot.check_apply(hello_remove)
        self.chroot.check_apply(hello_install)


class TestPackageRemoval(TestCase):

    def test_installed(self):
        """ Try removing a package that is installed. """
        self.chroot.check_apply("""
            resources:
              - Package:
                  name: zip
            """)
        self.chroot.check_apply("""
            resources:
              - Package:
                  name: zip
                  policy: uninstall
            """)


