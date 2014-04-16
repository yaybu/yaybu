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
from .local import LocalComputeLayer, NodeState


def vmrun(*args):
    return SubRunner(command_name="vmrun", args=args)

startvm = vmrun("start", "{name}", "gui")
stopvm = vmrun("stop", "{name}", "hard")
deletevm = vmrun("deleteVM", "{name}")
readVariable = vmrun("readVariable", "{name}", "guestVar", "{variable}")


class VMWareLayer(LocalComputeLayer):

    system = "vmware"

    def start(self):
        startvm(name=self.node.id)
        self.state = NodeState.RUNNING

    def create_args(self):
        return dict(vmx=self.original.params.vmx.as_dict(default=None))

    def destroy(self):
        stopvm(name=self.node.id)
        deletevm(name=self.node.id)
        shutil.rmtree(os.path.dirname(self.node.id))

    def test(self):
        return startvm.pathname is not None

    @property
    def public_ip(self):
        return readVariable(name=self.node.id, variable="ip").strip()

