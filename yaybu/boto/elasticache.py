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
from boto.exceptions import EC2ResponseError, BotoServerError

from yaybu.boto.base import BotoResource


class CacheSecurityGroup(BotoResource):

    module = boto.elasticache

    def create(self):
        name = self.params.name.as_string()
        description = self.params.description.as_string(default=name)
        with self.root.ui.throbber("Creating CacheSecurityGroup '%s'" % name):
            self.connection.create_dbsecurity_group(name, description)
        return True

    def update(self, existing):
        name = self.params.name.as_string()
        description = self.params.description.as_string(default=name)
        if existing.description != description:
            changed = True
        if changed:
            with self.root.ui.throbber("Updating CacheSecurityGroup '%s'" % name):
                self.connection.update_dbsecurity_group(name, description)
        return changed

    def apply(self):
        name = self.params.name.as_string()
        try:
            groups = self.connection.describe_cache_security_groups(name)
        except BotoServerError as e:
            if e.status != 404:
                raise
            return self.create_group()
        else:
            return self.update_group(groups[0])


class CacheSecurityGroupIngress(BotoResource):

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

        cache_group_name = self.params.to.as_string()

        try:
            response = self.connection.describe_cache_security_groups(cache_group_name)
            result = response['DescribeCacheSecurityGroupsResponse']['DescribeCacheSecurityGroupsResult']['CacheSecurityGroups'][0]
        except BotoServerError as e:
            if e.status != 404:
                print "No such CacheSecurityGroup '%s'" % cache_group_name
                return
            raise

        if filter(lambda x: x['EC2SecurityGroupName'] == ec2_group.name, result['EC2SecurityGroups']):
            return

        with self.root.ui.throbber("Creating CacheSecurityGroupIngress ('%s' -> '%s')" % (ec2_group.name, cache_group_name)):
            self.connection.authorize_cache_security_group_ingress(cache_group_name, ec2_group.name, ec2_group.owner_id)
            # FIXME: Ideally wait for Status to shift from Status=='authorizing' to Status=='authorized'


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
