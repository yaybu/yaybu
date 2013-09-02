# coding=utf-8

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


import unittest
from yaybu.provisioner.providers.service.upstart import _UpstartServiceMixin

class TestUpstartParser(unittest.TestCase):

    """ Tests our ability to handle output from /sbin/status """

    def parse(self, block):
        u = _UpstartServiceMixin()
        return list(u._parse_status_output(block))

    def test_multiple(self):
        lines = [
            "network-interface-security (network-manager) start/running",
            "network-interface-security (network-interface/eth0) start/running",
            "network-interface-security (network-interface/lo) start/running",
            "network-interface-security (networking) start/running",
            ]
        output = self.parse("\n".join(lines))

        self.assertEqual(len(output), 4)
        self.assertEqual(output[1].name, "network-interface/eth0")
        self.assertEqual(output[2].goal, "start")
        self.assertEqual(output[3].status, "running")

    def test_with_instance_name(self):
        output = self.parse("network-interface-security (network-manager) start/running\n")

        self.assertEqual(len(output), 1)
        self.assertEqual(output[0].name, "network-manager")
        self.assertEqual(output[0].goal, "start")
        self.assertEqual(output[0].status, "running")

    def test_start_running_with_pid(self):
        output = self.parse("ssh start/running, process 1234\n")

        self.assertEqual(len(output), 1)
        self.assertEqual(output[0].name, "ssh")
        self.assertEqual(output[0].goal, "start")
        self.assertEqual(output[0].status, "running")

    def test_stop_waiting_no_pid(self):
        output = self.parse("hwclock stop/waiting\n")

        self.assertEqual(len(output), 1)
        self.assertEqual(output[0].name, "hwclock")
        self.assertEqual(output[0].goal, "stop")
        self.assertEqual(output[0].status, "waiting")

