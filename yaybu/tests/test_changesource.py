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

from yaybu import error
from yaybu.tests.base import TestCase

GIT_LS_REMOTE = """
e8f51afcbfa78b077b5e91797cdd77c35350122f    HEAD
e8f51afcbfa78b077b5e91797cdd77c35350122f    refs/heads/master
352f0dcc87e6f64d9ae83cae3bf696b8c69a3987    refs/tags/3.0
b33e819fbdf0115f6e367d79716c1c1633afd00b    refs/tags/3.0^{}
""".strip()


class TestChangeSource(TestCase):

    def setUp(self):
        patcher = mock.patch("yaybu.changesource.subprocess")
        self.subprocess = patcher.start()
        self.addCleanup(patcher.stop)
        self.popen = self.subprocess.Popen

    def test_get_current_branch(self):
        self.popen.return_value.communicate.return_value = [GIT_LS_REMOTE, ""]

        self.assertRaises(error.NothingChanged, self.up, """
            new GitChangeSource as mychangesource:
               repository: /nowhere
               polling-interval: 0

            new Printer as myprinter:
                message: {{ mychangesource.master }}
            """)
