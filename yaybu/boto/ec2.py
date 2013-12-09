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

from __future__ import absolute_import

import boto.ec2
from boto.exception import EC2ResponseError

from yaybu.boto.base import BotoResource


class EC2SecurityGroup(BotoResource):

    module = boto.ec2

    def create(self):
        name = self.params.name.as_string()
        description = self.params.description.as_string(default=name)
        with self.root.ui.throbber("Creating SecurityGroup '%s'" % name):
            if not self.root.simulate:
                self.connection.create_security_group(name, description)
        return True

    def update(self, existing):
        name = self.params.name.as_string()
        description = self.params.description.as_string(default=name)
        changed = False
        if existing.description != description:
            changed = True
        if changed:
            with self.root.ui.throbber("Updating SecurityGroup '%s'" % name):
                if not self.root.simulate:
                    self.connection.update_security_group(name, description)
        return changed

    def apply(self):
        if self.root.readonly:
            return

        name = self.params.name.as_string()
        try:
            groups = self.connection.get_all_security_groups(groupnames=name)
        except EC2ResponseError as e:
            if e.error_code != "InvalidGroup.NotFound":
                raise
            group = self.create()
            changed = True
        else:
            group = groups[0]
            changed = self.update(group)

        # FIXME: This needs to suck less
        self.root.changelog.changed = self.root.changelog.changed or True

        return changed

    def destroy(self):
        name = self.params.name.as_string()

        try:
            self.connection.get_all_security_groups(groupnames=name)
        except EC2ResponseError as e:
            if e.error_code == "InvalidGroup.NotFound":
                return
            raise

        with self.root.ui.throbber("Deleting SecurityGroup '%s'" % name):
            self.connection.delete_security_group(name)
