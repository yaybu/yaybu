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
from boto.exception import BotoServerError

from yaybu.boto.base import BotoResource


class EC2SecurityGroup(BotoResource):

    module = boto.ec2

    def create(self):
        name = self.params.name.as_string()
        description = self.params.description.as_string(default=name)
        with self.root.ui.throbber("Creating SecurityGroup '%s'" % name):
            self.connection.create_security_group(name, description)
        return True

    def update(self, existing):
        name = self.params.name.as_string()
        description = self.params.description.as_string(default=name)
        if existing.description != description:
            changed = True
        if changed:
            with self.root.ui.throbber("Updating SecurityGroup '%s'" % name):
                self.connection.update_security_group(name, description)
        return changed

    def apply(self):
        name = self.params.name.as_string()
        try:
            groups = self.connection.get_all_security_groups(groupnames=name)
        except BotoServerError as e:
            if e.status != 404:
                raise
            return self.create_group()
        else:
            return self.update_group(groups[0])
