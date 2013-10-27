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

import mock

from yay import errors

from yaybu.tests.base import TestCase


class TestHeroku(TestCase):

    def setUp(self):
        patcher = mock.patch("yaybu.heroku.heroku")
        self.addCleanup(patcher.stop)
        patcher.start()

    def test_validate_no_credentials(self):
        self.assertRaises(errors.TypeError, self.up, """
            new Heroku as myheroku:
                application_id: foo-bar
            """)

    def test_validate_username_no_password(self):
        self.assertRaises(errors.TypeError, self.up, """
            new Heroku as myheroku:
                application_id: foo-bar
                username: freddy
            """)

    def test_validate_password_no_username(self):
        self.assertRaises(errors.TypeError, self.up, """
            new Heroku as myheroku:
                application_id: foo-bar
                password: penguin55
            """)

    def test_username_password(self):
        self._up("""
            new Heroku as myheroku:
                application_id: foo-bar
                username: freddy
                password: penguin55
            """)

    def test_add_addon(self):
        self._up("""
            new Heroku as myheroku:
                application_id: foo-bar
                username: freddy
                password: penguin55
                addons:
                  - loggly:mole
            """)

    def test_add_configuration(self):
        self._up("""
            new Heroku as myheroku:
                application_id: foo-bar
                username: freddy
                password: penguin55
                config:
                    DATABASE_URL: postgresql://username:password@localhost/db12346
            """)

    def test_set_scaling(self):
        self._up("""
            new Heroku as myheroku:
                application_id: foo-bar
                username: freddy
                password: penguin55
                scale:
                    web: 5
            """)

    def test_add_domain(self):
        self._up("""
            new Heroku as myheroku:
                application_id: foo-bar
                username: freddy
                password: penguin55
                domains:
                    - example.com
            """)

    def test_add_collaborator(self):
        self._up("""
            new Heroku as myheroku:
                application_id: foo-bar
                username: freddy
                password: penguin55
                collaborators:
                    - nobody@example.com
            """)
