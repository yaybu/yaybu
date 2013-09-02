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

import os
import sys
from yaybu.provisioner.tests.fixture import TestCase
from yaybu.core import error


class TestWatched(TestCase):

    def test_watched(self):
        self.chroot.check_apply("""
            resources:
                - Execute:
                    name: test_watched
                    command: touch /watched-file
                    creates: /watched-file
                    watch:
                      - /watched-file
                - Execute:
                    name: test_output
                    command: touch /event-triggered
                    creates: /event-triggered
                    policy:
                        execute:
                            when: watched
                            on: File[/watched-file]
            """)
        self.failUnlessExists("/event-triggered")

