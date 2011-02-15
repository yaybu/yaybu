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
from yaybu.resources import filesystem as resource
from yaybu.providers import filesystem
import os
from yaybu.core import shell

class TestFile(unittest.TestCase):

    def setUp(self):
        if not os.path.exists("test_file"):
            os.mkdir("test_file")

    def test_template(self):
        r = resource.File(
            name="test_file/test_template.out",
            template="package://yaybu.providers/tests/template1.j2",
            template_args={"foo": "this is foo", "bar": 42}
            )
        p = filesystem.File(r, None)
        p.action_create(shell.Shell())


