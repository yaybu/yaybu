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

import optparse, sys, logging

import yay

from yaybu.core.shell import Shell
from yaybu.core.resource import MetaResource

logging.basicConfig(stream=sys.stdout,level=logging.DEBUG)


class LoaderError(Exception):
    pass


class Runner(object):

    def __init__(self, registry=None):
        self.resources = []
        self.registry = registry or MetaResource.resources

    def create_resource(self, typename, instance):
        unicode_hack = dict((key.encode('utf-8'), item) for (key, item) in instance.iteritems())
        kls = self.registry[typename](**unicode_hack)
        self.resources.append(kls)

    def create_resources_of_type(self, typename, instances):
        # Create a Resource object for each item
        for instance in instances:
            self.create_resource(typename, instance)

    def create_resources(self, resources):
        for resource in resources:
            if len(resource.keys()) > 1:
                raise LoaderError("Too many keys in list item")

            typename, instances = resource.items()[0]

            if not isinstance(instances, list):
                instances = [instances]

            self.create_resources_of_type(typename, instances)

    def run(self):
        parser = optparse.OptionParser()
        parser.add_option("-s", "--simulate", default=False, action="store_true")
        opts, args = parser.parse_args()

        config = yay.load_uri(args[0])

        self.create_resources(config.get("resources", []))

        shell = Shell(simulate=opts.simulate)

        for resource in self.resources:
            provider = resource.select_provider()
            provider.action_create(shell)

        return 0


def main():
    return Runner().run()

