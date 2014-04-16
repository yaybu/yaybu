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

import time
import os
import shutil

from yaybu.core.util import memoized
from ..util import SubRunner
from .local import LocalComputeLayer, NodeState

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

guestproperty = vboxmanage("guestproperty", "get", "{name}", "{property}")


class VBoxLayer(LocalComputeLayer):

    system = "vbox"

    def start(self):
        startvm(type="gui", name=self.node.id)
        self.state = NodeState.STARTING

    def create_args(self):
        return dict(modifyvm=self.original.params.modifyvm.as_dict(default=None))

    def destroy(self):
        unregistervm(name=self.node)
        shutil.rmtree(os.path.dirname(self.node))
        self.node = None
        self.state = NodeState.EMPTY

    def test(self):
        return startvm.pathname is not None

    @property
    def public_ip(self):
        s = guestproperty(name=self.node.id, property="/VirtualBox/GuestInfo/Net/0/V4/IP")
        if s.startswith("Value: "):
            # Value: 10.0.2.15
            return s.split(" ", 1)[1]
