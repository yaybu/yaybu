# Copyright 2012 Isotoma Limited
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
import subprocess
import logging

from libcloud.compute import base


class VMWareNode(base.Node):

    logger = logging.getLogger("yaybu.roles.compute.vmware.VMWareNode")

    def __init__(self, provider, vmx):
        self.provider = provider
        self.vmx = vmx

    def _action(self, action, *params):
        return self.provider._action(action, self.vmx, *params)

    def start(self):
        self._action("start", "nogui")

    def stop(self):
        self._action("stop", "hard")

    def reboot(self):
        self._action("reset", "hard")

    def get_ip_address(self):
        return self._action("readVariable", "guestVar", "ip")


class VMWareDriver(base.NodeDriver):

    logger = logging.getLogger("yaybu.roles.compute.vmware.VMWareDriver")

    def _find_vmrun(self):
        known_locations = [
            "/Applications/VMWare Fusion.app/Contents/Library",
            ]
        for dir in known_locations:
            path = os.path.join(dir, "vmrun")
            if os.path.exists(path):
                return path
        raise NotSupported

    def _action(self, *params):
        command = [self._find_vmrun()] + list(params)
        self.logger.debug(command)
        p = subprocess.Popen([self._find_vmrun()] + list(params), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()
        self.logger.debug(command)
        return stdout

    def list_images(self, location=None):
        return []

    def list_sizes(self, location=None):
        return []

    def list_locations(self):
        return []

    def list_nodes(self):
        nodes = []
        for line in self._action("list").splitlines():
            if line.startswith("/") and os.path.exists(line):
                n = VMWareNode(self, line.strip())
                nodes.append(n)
        return nodes

    def create_node(self, name, size, image):
        source = image.id
        if not os.path.exists(source):
            raise LibcloudError("Base image is not valid")

        target = "/tmp/example.vmx"

        self._action("clone", source, target)

        node = VMWareNode(self, target)
        node.start()
        return node

    def reboot_node(self, node):
        node.reboot()

    def destroy_node(self, node):
        node.destroy()


