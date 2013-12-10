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

import json

import boto.iam

from yay import errors
from yaybu.boto.base import BotoResource


class IAMRole(BotoResource):

    default_region = 'universal'
    module = boto.iam

    def create(self):
        name = self.params.name.as_string()
        with self.root.ui.throbber("Creating IAMRole '%s'" % name):
            if not self.root.simulate:
                return self.connection.create_role(
                    name
                )['create_role_response']['create_role_result']['role']

        # A dummy for simulate mode
        return {'list_roles_response': {'list_roles_result': {'roles': [{'role_name': name}]}}}

    def apply(self):
        if self.root.readonly:
            return

        name = self.params.name.as_string()
        changed = False

        roles = [r for r in self.connection.list_roles()['list_roles_response']['list_roles_result']['roles'] if r['role_name'] == name]
        if not roles:
            self.create()
            changed = True

        existing_policy_names = set(p for p in self.connection.list_role_policies(name)['list_role_policies_response']['list_role_policies_result']['policy_names'])
        try:
            new_policy_names = set(k for k in self.params.policies.keys())
        except errors.NoMatching:
            new_policy_names = set()

        for policy in (existing_policy_names - new_policy_names):
            with self.root.ui.throbber("Removing policy '%s'" % policy):
                self.connection.delete_role_policy(name, policy)
            changed = True

        for policy in (new_policy_names - existing_policy_names):
            with self.root.ui.throbber("Adding policy '%s'" % policy):
                policies = self.params.policies[policy].as_list()
                policy_str = json.dumps({"Statement": policies})
                self.connection.put_role_policy(name, policy, policy_str)
            changed = True

        # FIXME: Get intersection of policies and check if updates required

        self.root.changelog.changed = self.root.changelog.changed or changed
        return changed

    def destroy(self):
        name = self.params.name.as_string()

        roles = [r for r in self.connection.list_roles()['list_roles_response']['list_roles_result']['roles'] if r['role_name'] == name]
        if not roles:
            return

        for policy in self.connection.list_role_policies(name)['list_role_policies_response']['list_role_policies_result']['policy_names']:
            with self.root.ui.throbber("Removing policy '%s'" % policy):
                self.connection.delete_role_policy(name, policy)

        with self.root.ui.throbber("Deleting IAMRole '%s'" % name):
            self.connection.delete_role(name)
