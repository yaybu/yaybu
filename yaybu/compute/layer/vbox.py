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

from .local import LocalComputeLayer
from yaybu.compute.image.vbox import test_connection

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


class VBoxLayer(LocalComputeLayer):

    wait_delay = 300

    system = "vbox"

    def options(self):
        return self.original.params.modifyvm.as_dict(default=None)

    def test(self):
        return test_connection()
