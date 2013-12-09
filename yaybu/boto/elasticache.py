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

import boto.elasticache
from boto.exception import EC2ResponseError, BotoServerError

from yay import errors

from yaybu.boto.base import BotoResource


class CacheSecurityGroup(BotoResource):

    module = boto.elasticache

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
        with self.root.ui.throbber("Creating CacheSecurityGroup '%s'" % name):
            response = self.connection.create_cache_security_group(name, description)
            result = response['CreateCacheSecurityGroupResponse']['CreateCacheSecurityGroupResult']['CacheSecurityGroup']
        return result

    def update(self, existing):
        name = self.params.name.as_string()
        description = self.params.description.as_string(default=name)
        changed = False
        if existing['Description'] != description:
            changed = True
        if changed:
            with self.root.ui.throbber("Updating CacheSecurityGroup '%s'" % name):
                self.connection.update_cache_security_group(name, description)
        return changed

    def apply(self):
        if self.root.readonly:
            return

        name = self.params.name.as_string()
        try:
            response = self.connection.describe_cache_security_groups(name)
        except BotoServerError as e:
            if e.status != 404:
                raise
            group = self.create()
            changed = True
        else:
            group = response['DescribeCacheSecurityGroupsResponse']['DescribeCacheSecurityGroupsResult']['CacheSecurityGroups'][0]
            changed = self.update(group)

        current = set(self.clean_allowed())
        next = set([(g['EC2SecurityGroupName'], g['EC2SecurityGroupOwnerId']) for g in group['EC2SecurityGroups']])

        for group in (current - next):
            with self.root.ui.throbber("Authorizing ingress (%s -> %s)" % (group[0], name)):
                if not self.root.simulate:
                    self.connection.authorize_cache_security_group_ingress(
                        name,
                        group[0],
                        group[1],
                    )

                # FIXME: Ideally wait for Status to shift from Status=='authorizing' to Status=='authorized'
                changed = True

        for group in (next - current):
            with self.root.ui.throbber("Deauthorizing ingress (%s -> %s)" % (group[0], name)):
                if not self.root.simulate:
                    self.connection.revoke_cache_security_group_ingress(
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
            self.connection.describe_cache_security_groups(name)
        except BotoServerError as e:
            if e.status == 404:
                return
            raise

        with self.root.ui.throbber("Deleting CacheSecurityGroup '%s'" % name):
            self.connection.delete_cache_security_group(name)


class CacheCluster(BotoResource):

    module = boto.elasticache

    def create(self):
        # FIXME: Actually get theses settings from self.params
        response = self.connection.create_cache_cluster(
            cache_cluster_id=id,
            num_cache_node=1,
            cache_node_type='cache.t1.micro',
            engine='redis',
            port=6379,
            cache_security_group_names=[],
        )
        return response['CreateCacheClusterResponse']['CreateCacheClusterResult']['CacheCluster']

    def update(self, existing):
        # FIXME: Update cache cluster settings here
        pass

    def apply(self):
        try:
            response = self.connection.describe_cache_clusters(cache_cluster_id=id, show_cache_node_info=True)
            result = response['DescribeCacheClustersResponse']['DescribeCacheClustersResult']['CacheClusters'][0]
        except BotoServerError as e:
            if e.status != 404:
                raise
            self.create()
        else:
            self.update(result)

        if result['CacheClusterStatus'] != 'available':
            with self.root.ui.throbber("Waiting for CacheCluster to be in state 'available'") as throbber:
                while result['CacheClusterStatus'] != 'available':
                    response = self.connection.describe_cache_clusters(cache_cluster_id=id, show_cache_node_info=True)
                    result = response['DescribeCacheClustersResponse']['DescribeCacheClustersResult']['CacheClusters'][0]
                    time.sleep(1)
                    throbber.throb()

        # FIXME: Extract Endpoint and other outputs and place in graph
