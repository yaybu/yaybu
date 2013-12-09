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

import time

import boto.rds
from boto.exception import EC2ResponseError, BotoServerError

from yay import errors

from yaybu.boto.base import BotoResource


class DBSecurityGroup(BotoResource):

    module = boto.rds

    def clean_allowed(self):
        from boto.ec2 import connect_to_region
        c = connect_to_region('eu-west-1')

        allowed = []

        try:
            groups = self.params.allowed.get_iterable()
        except errors.NoMatching:
            groups = []

        for group in groups:
            try:
                name = group.as_string()
            except errors.TypeError:
                name = group.get_key("name").as_string()

            try:
                groups = c.get_all_security_groups(groupnames=[name])
                g = groups[0]
            except EC2ResponseError:
                # FIXME: Don't raise if simulating
                raise TypeError("No such EC2 SecurityGroup '%s'" % name)

            allowed.append((g.name, g.owner_id))

        return allowed

    def create(self):
        name = self.params.name.as_string()
        description = self.params.description.as_string(default=name)
        with self.root.ui.throbber("Creating DBSecurityGroup '%s'" % name):
            return self.connection.create_dbsecurity_group(name, description)
    
    def update(self, existing):
        name = self.params.name.as_string()
        description = self.params.description.as_string(default=name)
        changed = False
        if existing.description != description:
            changed = True
        if changed:
            with self.root.ui.throbber("Updating DBSecurityGroup '%s'" % name):
                self.connection.update_dbsecurity_group(name, description)
        return changed

    def apply(self):
        if self.root.readonly:
            return

        name = self.params.name.as_string()
        try:
            groups = self.connection.get_all_dbsecurity_groups(groupname=name)
            group = groups[0]
        except BotoServerError as e:
            if e.status != 404:
                raise
            group = self.create()
            changed = True
        else:
            changed = self.update(group)

        current = set(self.clean_allowed())
        next = set([(g.name, g.owner_id) for g in group.ec2_groups])

        for group in (current - next):
            with self.root.ui.throbber("Authorizing ingress (%s -> %s)" % (group[0], name)):
                if not self.root.simulate:
                    self.connection.authorize_dbsecurity_group(
                        name,
                        ec2_security_group_name=group[0],
                        ec2_security_group_owner_id=group[1],
                    )

                # FIXME: Ideally wait for Status to shift from Status=='authorizing' to Status=='authorized'
                changed = True

        for group in (next - current):
            with self.root.ui.throbber("Deauthorizing ingress (%s -> %s)" % (group[0], name)):
                if not self.root.simulate:
                    self.connection.revoke_dbsecurity_group(
                        name,
                        ec2_security_group_name=group[0],
                        ec2_security_group_owner_id=group[1],
                    )
                #FIXME: Wait for it to disappear from output
                changed = True

        return changed

    def destroy(self):
        name = self.params.name.as_string()

        try:
            self.connection.get_all_dbsecurity_groups(groupname=name)
        except BotoServerError as e:
            if e.status == 404:
                return
            raise

        with self.root.ui.throbber("Deleting DBSecurityGroup '%s'" % name):
            self.connection.delete_dbsecurity_group(name)


class DBInstance(BotoResource):

    module = boto.rds

    def create(self):
        name = self.params.name.as_string()
        instance = self.connection.create_dbinstance(
            name, 5, 'db.t1.micro', 'root', 'bototestpw')
        return instance

    def apply(self):
        name = self.params.name.as_string()

        try:
            instances = self.connection.get_all_dbinstances(name)
            instance = instances[0]
        except BotoServerError as e:
            if e.status != 404:
                raise
            instance = self.create()
            changed = True
        else:
            changed = self.update(instance)

        if instance.status != 'available':
            # FIXME: add throbber
            while instance.status != 'available':
                time.sleep(1)
                instances = self.connection.get_all_dbinstances(name)
                instance = instances[0]

        return changed
