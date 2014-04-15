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

import os

import time
import shutil

from .local import LocalComputeLayer

from ..util import SubRunner

def vboxmanage(*args):
    return SubRunner(command_name="VBoxManage", args=args)


startvm = vboxmanage("startvm",
                     "--type", "{type}",
                     "{name}")

unregistervm = vboxmanage("unregistervm",
                          "{name}", "--delete")


class VBoxLayer(LocalComputeLayer):

    def _find_vm(self, name):
        for vm in self.machines.instances("vbox"):
            # find it
            return vm
        return None

    def load(self, name):
        vm = self._find_vm(name)
        if vm is not None:
            startvm(type="gui", name=self.node)

    def create(self):
        # TODO THIS IS THE OLD CODE
        state = kwargs.pop("state")
        kwargs.update(image.extra)
        auth = self._get_and_check_auth(kwargs.pop("auth", None))
        base_image = self._get_source(image)
        machine = self.machines.create_node("vbox", base_image, state, auth=auth, **kwargs)
        node = Node(machine.id, name, NodeState.PENDING, None, None, self)
        self.ex_start(node)
        return node

    def destroy(self):
        unregistervm(name=self.node)
        shutil.rmtree(os.path.dirname(self.node))

    def wait(self):
        # see the old _decorate_node
        pass

    def test(self):
        raise NotImplementedError()

    def domain(self):
        raise NotImplementedError()

    def fqdn(self):
        raise NotImplementedError()

    def hostname(self):
        raise NotImplementedError()

    def location(self):
        raise NotImplementedError()

    def name(self):
        raise NotImplementedError()

    def private_ip(self):
        raise NotImplementedError()

    def private_ips(self):
        raise NotImplementedError()

    def public_ip(self):
        raise NotImplementedError()

    def public_ips(self):
        raise NotImplementedError()
