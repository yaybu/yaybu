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

from yaybu.provisioner.provider import Provider
from yaybu.provisioner import resources


class Mounted(Provider):

    policies = (resources.checkout.CheckoutSyncPolicy,)

    @classmethod
    def isvalid(self, policy, resource, yay):
        return resource.scm in ("dummy", "mounted", "mount")

    def apply(self, context, output):
        for w in self.resource.watch.as_list():
            if context.transport.exists(w):
                context.change(ShellCommand(["touch", "-ac", w]))

        return True

