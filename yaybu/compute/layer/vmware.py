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

import shutil
import os
from yaybu.core.util import memoized
from ..util import SubRunner
from .local import LocalComputeLayer


def vmrun(*args):
    return SubRunner(command_name="vmrun", args=args)

startvm = vmrun("start", "{name}", "gui")
stopvm = vmrun("stop", "{name}", "hard")
deletevm = vmrun("deleteVM", "{name}")
readVariable = vmrun("readVariable", "{name}", "guestVar", "{variable}")


class VMWareLayer(LocalComputeLayer):

    @memoized
    @property
    def vmx(self):
        return self.original.params.vmx.as_dict(default=None)

    def load(self, name):
        for vm in self.machines.instances("vmware"):
            if vm.name == name:
                self.node = vm
                startvm(name=self.node.id)

    def create(self):
        base_image = self.machines.fetch(self.image)
        self.pending_node = self.machines.create_node(
            name=self.original.params.name.as_string(),
            distro=self.image.distro,
            system="vmware",
            base_image=base_image,
            state=self.original.state,
            auth=self.auth,
            hardware=self.hardware,
            vmx=self.vmx)
        startvm(name=self.pending_node.id)

    def destroy(self):
        stopvm(name=self.node.id)
        deletevm(name=self.node.id)
        shutil.rmtree(os.path.dirname(self.node.id))

    def wait(self):
        """ Add ips. Returns True if it successfully decorated it, False if
        it failed and None if the node was not running. """
        ip = readVariable(name=self.pending_node.id, variable="ip")
        if not ip:
            return
        self.node = self.pending_node
        self.pending_node = None

    def test(self):
        return startvm.pathname is not None

    @property
    def domain(self):
        raise NotImplementedError()

    @property
    def fqdn(self):
        raise NotImplementedError()

    @property
    def hostname(self):
        raise NotImplementedError()

    @property
    def location(self):
        raise NotImplementedError()

    @property
    def name(self):
        if self.node is not None:
            return self.node.name
        raise ValueError("No active node")

    @property
    def private_ip(self):
        raise NotImplementedError()

    @property
    def private_ips(self):
        raise NotImplementedError()

    @property
    def public_ip(self):
        raise NotImplementedError()

    @property
    def public_ips(self):
        raise NotImplementedError()
