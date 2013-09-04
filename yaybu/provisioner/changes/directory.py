# Copyright 2013 Isotoma Limited
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

from yaybu import changes
from .execute import ShellCommand
from .attributes import AttributeChanger


class EnsureDirectory(changes.Change):

    def __init__(self, path, owner, group, mode, recursive=False):
        self.path = path
        self.owner = owner
        self.group = group
        self.mode = mode
        self.recursive = recursive

    def apply(self, context, renderer):
        self.changed = False
        if not context.transport.exists(self.path):
            command = ["/bin/mkdir"]
            if self.recursive:
                command.append("-p")
            command.append(self.path.decode("utf-8"))
            context.change(ShellCommand(command))
            self.changed = True

        ac = context.change(AttributeChanger(
            self.path,
            self.owner,
            self.group,
            self.mode
            ))

        self.changed = self.changed or ac.changed

        return self.changed

