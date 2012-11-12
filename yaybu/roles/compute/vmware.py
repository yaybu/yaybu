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

# This driver presents a libcloud interface around vmrun - the command line API
# for controlling VMWare VM's.

# Base image notes:
#1. Install vmware tools from packages.vmware.com/tools - the latest esx ones work with vmware fusion
#2. Don't forget to delete the persistent net rules
#3. There needs to be a user with a password/key that can get to root without sudo requiring a passphrase.


import os
import glob
import shutil
import subprocess
import logging

from libcloud.compute import base
from libcloud.compute.types import NodeState
from libcloud.common.types import LibcloudError


class VMWareNode(base.Node):

    logger = logging.getLogger("yaybu.roles.compute.vmware.VMWareNode")

    def _action(self, action, *params):
        return self.driver._action(action, self.id, *params)

    def start(self):
        self._action("start", "nogui")

    def stop(self):
        self._action("stop", "hard")

    def reboot(self):
        self._action("reset", "hard")
        self.state = NodeState.REBOOTING

    def destroy(self):
        self.stop()
        self._action("deleteVM")
        shutil.rmtree(os.path.dirname(self.id))

    def get_ip_address(self):
        return self._action("readVariable", "guestVar", "ip").strip()

    def _refresh(self):
        public_ip = self.get_ip_address()
        if public_ip:
            self.public_ips = [public_ip]
            self.state = NodeState.RUNNING
        else:
            self.state = NodeState.UNKNOWN


class VMWareDriver(base.NodeDriver):

    logger = logging.getLogger("yaybu.roles.compute.vmware.VMWareDriver")

    type = 99
    name = "vmware"

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
        self.logger.debug(stdout)
        if p.returncode != 0:
            raise LibcloudError("Call to vmrun failed with exit code %d\nCall: %s\n%s" % (p.returncode, command, stderr))
        return stdout

    def list_images(self, location=None):
        vm_locations = [
            os.path.join(os.path.expanduser("~/Documents/Virtual Machines/"), "*", "*.vmx"),
            os.path.join(os.path.expanduser("~/Documents/Virtual Machines.localized/"), "*", "*.vmx"),
            ]

        locs = []
        for loc in vm_locations:
            for match in glob.glob(os.path.expanduser(loc)):
                locs.append(base.NodeImage(id=match, name="VMWare Image", driver=self))
        return locs

    def list_sizes(self, location=None):
        return []

    def list_locations(self):
        return []

    def list_nodes(self):
        nodes = []
        for line in self._action("list").splitlines():
            if line.startswith("/") and os.path.exists(line):
                n = VMWareNode(line.strip(), line.strip(), NodeState.UNKNOWN, None, None, self)
                n._refresh()
                nodes.append(n)
        return nodes

    def _manual_clone(self, source, target):
        self.logger.debug("Manually cloning '%s' to '%s'" % (source, target, ))
        src_path = os.path.dirname(source)
        target_path = os.path.dirname(target)

        shutil.copytree(src_path, target_path)

        # Mutate VMX file...
        os.rename(os.path.join(target_path, os.path.basename(source)),
            os.path.join(target_path, os.path.basename(target)))

    def create_node(self, name, size, image):
        source = image.id
        if not os.path.exists(source):
            raise LibcloudError("Base image is not valid")

        target = "/Users/john/example-image/example.vmx"

        if os.path.exists(os.path.dirname(target)):
            raise LibcloudError("Destination folder already exists: %s" % os.path.dirname(target))

        try:
            self._action("clone", source, target)
        except LibcloudError:
            self._manual_clone(source, target)

        if not os.path.exists(target):
            raise LibcloudError("Unable to create clone: '%s'" % target)

        node = VMWareNode(target, name, NodeState.PENDING, None, None, self)
        node.start()
        return node

    def reboot_node(self, node):
        node.reboot()

    def destroy_node(self, node):
        node.destroy()


