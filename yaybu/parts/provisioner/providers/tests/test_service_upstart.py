# coding=utf-8

import unittest
from yaybu.providers.service.upstart import _UpstartServiceMixin

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

