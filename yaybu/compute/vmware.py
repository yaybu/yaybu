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
from libcloud.compute.base import NodeAuthPassword, NodeAuthSSHKey
import json
import urllib2
import uuid
import datetime
import urlparse
import tempfile
from functools import partial
import time
import shutil
import hashlib

from libcloud.compute.base import NodeDriver, Node
from libcloud.compute.base import NodeState
from libcloud.compute.types import Provider


import zipfile
from yaybu.util import ZipFile
from yaybu.compute.process import Connection, Response

from .image.library import ImageLibrary


class VMRunError(LibcloudError):
    pass


class FileAlreadyExistsError(VMRunError):

    def __init__(self):
        self.value = "File or directory already exists"


class VMRunResponse(Response):

    def parse_error(self):
        if self.body == 'Error: The file already exists\n':
            raise FileAlreadyExistsError()
        super(VMRunResponse, self).parse_error()


class VMRunConnection(Connection):
    responseCls = VMRunResponse


# FIXME:
Provider.VMWARE = 99

class VMWareDriver(NodeDriver):

    """ This is an implementation of a libcloud driver for VMWare, that is
    used in preference to libvirt because it is better. """

    type = Provider.VMWARE
    name = "vmware"
    website = "http://www.vmware.com/products/fusion/"
    connectionCls = VMRunConnection
    features = {'create_node': ['ssh_key', 'password']}

    def __init__(self, yaybu_root="~/.yaybu", vmrun=None, hosttype=None):
        super(VMWareDriver, self).__init__(None)
        self.vmrun = vmrun or self._find_vmrun()
        self.hosttype = hosttype or self._find_hosttype()
        self.machines = ImageLibrary(root=yaybu_root)

    def ex_start(self, node):
        """
        Start a stopped node.

        @param node: Node which should be used
        @type  node: L{Node}

        @rtype: C{bool}
        """
        self._action("start", node.id, "nogui", capture_output=False)
        node.state = NodeState.RUNNING
        with self.yaybu_context.ui.throbber("Wait for VM to boot completely"):
            while not self._decorate_node(node):
                time.sleep(1)

    def _find_vmrun(self):
        known_locations = [
            "/Applications/VMWare Fusion.app/Contents/Library",
            "/usr/bin",
        ]
        for dir in known_locations:
            path = os.path.join(dir, "vmrun")
            if os.path.exists(path):
                return path
        raise LibcloudError(
            'VMWareDriver requires \'vmrun\' executable to be present on system')

    def _find_hosttype(self):
        default_hosttypes = [
            'ws',
            'fusion',
            'player',
        ]
        for hosttype in default_hosttypes:
            command = [self.vmrun, "-T", hosttype, "list"]
            try:
                self.connection.request(command)
            except LibcloudError:
                continue
            else:
                return hosttype
        raise LibcloudError(
            'VMWareDriver is unable to find a default host type. Please specify the hosttype argument')

    def _action(self, *params, **kwargs):
        capture_output = kwargs.get('capture_output', True)
        command = [self.vmrun, "-T", self.hosttype] + list(params)
        return (
            self.connection.request(
                command,
                capture_output=capture_output).body
        )

    def _guest_action(self, target, command, *params):
        self._action("-gu", target.username, "-gp", target.password,
                     command, target.id, *params,
                     capture_output=True)

    def list_images(self, location=None):
        raise NotImplementedError

    def list_sizes(self, location=None):
        raise NotImplementedError

    def list_locations(self):
        return []

    def _list_running(self):
        """ List running virtual machines """
        lines = iter(self._action("list").strip().splitlines())
        lines.next()  # Skip the summary line
        for line in lines:
            if not line.strip():
                continue
            yield line.strip()

    def _decorate_node(self, node):
        """ Add ips. Returns True if it successfully decorated it, False if
        it failed and None if the node was not running. """
        if node.state == NodeState.RUNNING:
            ip = self._action(
                "readVariable", node.id, "guestVar", "ip").strip()
            if ip:
                node.public_ips = [ip]
                return True
            return False
        return None

    def list_nodes(self):
        """ List all of the nodes the driver knows about. """
        nodes = []
        running = list(self._list_running())
        for vm in self.machines.instances("vmware"):
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

    def create_node(self, name, size, image, auth=None, **kwargs):
        """ Create a new VM from a template VM and start it.
        """

        auth = self._get_and_check_auth(auth)
        base_image = self._get_source(image)
        machine = self.machines.create_node("vmware", base_image, auth, name, size, **kwargs)
        node = Node(machine.id, name, NodeState.PENDING, None, None, self)
        self.ex_start(node)
        return node

    def reboot_node(self, node):
        self._action("reset", node.id, "hard")
        node.state = NodeState.REBOOTING

    def destroy_node(self, node):
        self._action("stop", node.id, "hard")
        self._action("deleteVM", node.id)
        shutil.rmtree(os.path.dirname(node.id))

    def ex_get_runtime_variable(self, node, variable):
        value = self._action(
            "readVariable", node.id, "runtimeConfig", variable)
        return value

    def ex_set_runtime_variable(self, node, variable, value):
        self._action(
            "writeVariable", node.id, "runtimeConfig", variable, value)

