# Copyright 2011 Isotoma Limited
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

import json


class EventState(object):

    """ Represents the current state of events """

    save_file = "events.saved"
    """ The file to save to.  This is touched by the runner. """


    overrides = {}
    """ A mapping of resource ids to the overridden policy name for that
    resource, if there is one. """

    def __init__(self, load=False):
        self.loaded = not load
        self.overrides = {}
        self.simulate = False

    def load(self):
        if self.loaded:
            return
        if self.transport.exists(self.save_file):
            self.overrides = json.loads(self.transport.get(self.save_file))
        self.loaded = True

    def override(self, resource, policy):
        self.load()
        self.overrides[resource.id] = policy
        self.save()

    def clear_override(self, resource):
        self.load()
        if resource.id in self.overrides:
            del self.overrides[resource.id]
            self.save()

    def overridden_policy(self, resource):
        """ Return the policy class for this resource, or None if there is not
        an overridden policy. """
        self.load()
        if resource.id in self.overrides:
            policy_name = self.overrides[resource.id]
            return resource.policies[policy_name]
        else:
            return None

    def save(self):
        if not self.simulate:
            data = json.dumps(self.overrides)
            self.transport.put(self.save_file, data)

