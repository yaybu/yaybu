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
from boto.exceptions import EC2ResponseError, BotoServerError

from yaybu.boto.base import BotoResource


class DBSecurityGroup(BotoResource):

    module = boto.rds

    def create(self):
        name = self.params.name.as_string()
        description = self.params.description.as_string(default=name)
        self.connection.create_dbsecurity_group(name, description)
        return True

    def update(self, existing):
        name = self.params.name.as_string()
        description = self.params.description.as_string(default=name)
        if existing.description != description:
            changed = True
        if changed:
            self.connection.update_dbsecurity_group(name, description)
        return changed

    def apply(self):
        name = self.params.name.as_string()
        try:
            groups = self.connection.get_all_security_groups(groupnames=[name])
        except EC2ResponseError:
            #FIXME: Check that this is actually a 'does not exist'
            return self.create()
        else:
            return self.update(groups[0])


class DBSecurityGroupIngress(BotoResource):

    module = boto.rds

    def apply(self):
        from boto.ec2 import connect_to_region
        c = connect_to_region('eu-west-1')

        ec2_group = self.params["from"].as_string()

        try:
            groups = c.get_all_security_groups(groupnames=[ec2_group])
        except EC2ResponseError:
            print "No such EC2 Security Group"
            return

        ec2_group = groups[0]

        db_group_name = self.params.to.as_string()

        try:
            groups = c.get_all_dbsecurity_groups(groupname=db_group_name)
        except BotoServerError as e:
            if e.status == 404:
                print "No such DBSecurityGroup '%s'" % db_group_name
                return
            raise

        if filter(lambda x: x.EC2SecurityGroupId == ec2_group.id, groups[0].ec2_groups):
            return

        print "Creating DBSecurityGroup"
        c.authorize_dbsecurity_group(
            db_group_name,
            ec2_security_group_name=ec2_group.name,
            ec2_security_group_owner_id=ec2_group.owner_id
        )

        # FIXME: Ideally wait for Status to shift from Status=='authorizing' to Status=='authorized'


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
