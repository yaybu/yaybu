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

import os
import shutil

from yaybu.core.util import memoized
from ..util import SubRunner
from .local import LocalComputeLayer

# createvm options to accomodate - Priority 1
# --memory <memorysize in MB> - CONFIGURATION
# --ioapic on|off   - ALWAYS ON
# --cpus <number> - CONFIGURATION

# createvm options to accomodate - Priority 2
# --pagefusion on|off
# --vram <vramsize in MB>
# --firmware bios|efi|efi32|efi64
# --cpuexecutioncap <1-100>

# other features to accomodate
# attaching additional IDE drives
# attaching additional SATA drives
# network settings
# shared folders


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

    @memoized
    @property
    def modifyvm(self):
        """ Take the parameters from the compute node and configure ourselves
        to create or run an instance """
        return self.original.params.modifyvm.as_dict(default=None)

    def create(self):
        pass
        # TODO THIS IS THE OLD CODE
        # state = kwargs.pop("state")
        # kwargs.update(image.extra)
        # auth = self._get_and_check_auth(kwargs.pop("auth", None))
        # base_image = self._get_source(image)
        # machine = self.machines.create_node("vbox", base_image, state, auth=auth, **kwargs)
        # node = Node(machine.id, name, NodeState.PENDING, None, None, self)
        # self.ex_start(node)
        # return node

    def destroy(self):
        unregistervm(name=self.node)
        shutil.rmtree(os.path.dirname(self.node))

    def wait(self):
        # see the old _decorate_node
        pass

    def test(self):
        return startvm.pathname is not None

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
