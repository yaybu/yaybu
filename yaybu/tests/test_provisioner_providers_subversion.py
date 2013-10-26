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
from yaybu.core.error import MissingDependency


class TestSubversion(TestCase):

    def test_missing_svn(self):
        self.assertRaises(MissingDependency, self.apply, """
           resources:
               - Package:
                   name: subversion
                   policy: uninstall

               - Checkout:
                   scm: subversion
                   name: /dest
                   repository: /source
                   branch: trunk
           """)

    def test_checkout(self):
        self.check_apply("""
            resources:
                - Checkout:
                    scm: subversion
                    name: /subversion
                    repository: https://github.com/isotoma/isotoma.recipe.django
                    branch: trunk
            """)
        self.failUnlessExists("/subversion/setup.py")

    def test_checkout_tag(self, tag="3.0.2"):
        self.check_apply("""
            resources:
                - Checkout:
                    scm: subversion
                    name: /subversion
                    repository: https://github.com/isotoma/isotoma.recipe.django
                    tag: %s
            """ % tag)

    def test_checkout_branch(self):
        self.check_apply("""
            resources:
                - Checkout:
                    scm: subversion
                    name: /subversion
                    repository: https://github.com/isotoma/isotoma.recipe.django
                    branch: branches/version3
            """)

    def test_change_to_branch(self):
        """Test change to branch after an initial checkout, and back again """
        self.test_checkout()
        self.test_checkout_branch()
        self.test_checkout()

    def test_change_trunk_to_tag(self):
        """Test change to tag after an initial checkout, and back again """
        self.test_checkout()
        self.test_checkout_tag()
        self.test_checkout()

    def test_change_tag_to_tag(self):
        self.test_checkout_tag()
        self.test_checkout_tag("3.1.6")
