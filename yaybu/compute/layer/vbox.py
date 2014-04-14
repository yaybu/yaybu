# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# This driver presents a libcloud interface around vmrun - the command line API
# for controlling VMWare VM's.

# Base image notes:
# 1. Install vmware tools from packages.vmware.com/tools - the latest esx ones work with vmware fusion
# 2. Don't forget to delete the persistent net rules
# 3. There needs to be a user with a password/key that can get to root
# without sudo requiring a passphrase.

import os

from libcloud.common.types import LibcloudError
import time
import shutil

from libcloud.compute.base import NodeDriver, Node
from libcloud.compute.base import NodeState
from libcloud.compute.types import Provider

from yaybu.compute.process import Connection

from .image.library import ImageLibrary


class VBoxError(LibcloudError):
    pass

# FIXME:
Provider.VBOX = 98


class VBoxDriver(NodeDriver):

    type = Provider.VBOX
    name = "vbox"
    website = "http://www.vmware.com/products/fusion/"
    connectionCls = Connection
    features = {'create_node': ['ssh_key', 'password']}

    def __init__(self, yaybu_root="~/.yaybu", vboxmanage=None):
        super(VBoxDriver, self).__init__(None)
        self.vboxmanage = vboxmanage or self._find_vboxmanage()
        self.machines = ImageLibrary(root=yaybu_root)

    def ex_start(self, node):
        """
        Start a stopped node.

        @param node: Node which should be used
        @type  node: L{Node}

        @rtype: C{bool}
        """
        self._action("startvm", "--type", "gui", node.id)
        node.state = NodeState.RUNNING
        with self.yaybu_context.ui.throbber("Wait for VM to boot completely"):
            while not self._decorate_node(node):
                time.sleep(1)

    def _find_vboxmanage(self):
        known_locations = [
            "/usr/bin",
        ]
        for dir in known_locations:
            path = os.path.join(dir, "VBoxManage")
            if os.path.exists(path):
                return path
        raise LibcloudError(
            'VBoxDriver requires \'VBoxManage\' executable to be present on system')

    def _action(self, *params, **kwargs):
        command = [self.vboxmanage] + list(params)
        return (
            self.connection.request(command).body
        )

    def list_images(self, location=None):
        raise NotImplementedError

    def list_sizes(self, location=None):
        raise NotImplementedError

    def list_locations(self):
        return []

    def _list_running(self):
        """ List running virtual machines """
        # TODO
        return []

    def _decorate_node(self, node):
        """ Add ips. Returns True if it successfully decorated it, False if
        it failed and None if the node was not running. """
        if node.state == NodeState.RUNNING:
            # find the IP somehow!
            # node.public_ips = [ip]
            return True
        return None

    def list_nodes(self):
        """ List all of the nodes the driver knows about. """
        nodes = []
        running = list(self._list_running())
        for vm in self.machines.instances("vbox"):
            state = NodeState.RUNNING if vm.id in running else NodeState.UNKNOWN
            n = Node(vm.id, vm.id, state, None, None, self)
            self._decorate_node(n)
            nodes.append(n)
        return nodes

    def _image_smells_remote(self, imageid):
        remote_smells = ('http://', 'https://', 'file://')
        for smell in remote_smells:
            if imageid.startswith(smell):
                return True
        return False

    def _get_source(self, image):
        """ If the source looks like it is remote then fetch the image and
        extract it into the library directory, otherwise use it directly. """
        if "distro" in image.extra:
            source = self.machines.get_canonical(distro=image.extra['distro'], release=image.extra['release'], arch=image.extra['arch'], context=self.yaybu_context)
        elif self._image_smells_remote(image.id):
            source = self.machines.get_remote(image.id, context=self.yaybu_context)
        else:
            source = os.path.expanduser(image.id)
        if not os.path.exists(source):
            raise LibcloudError("Base image %s not found" % source)
        return source

    def create_node(self, name, image, **kwargs):
        """ Create a new VM from a template VM and start it.
        """

        state = kwargs.pop("state")
        kwargs.update(image.extra)
        auth = self._get_and_check_auth(kwargs.pop("auth", None))
        base_image = self._get_source(image)
        machine = self.machines.create_node("vbox", base_image, state, auth=auth, **kwargs)
        node = Node(machine.id, name, NodeState.PENDING, None, None, self)
        self.ex_start(node)
        return node

    def reboot_node(self, node):
        self._action("controlvm", node.id, "reset")
        node.state = NodeState.REBOOTING

    def destroy_node(self, node):
        self._action("unregistervm", node.id, "--delete")
        shutil.rmtree(os.path.dirname(node.id))
