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

import optparse, os, sys, logging

import yay

from yaybu.core.shell import Shell
from yaybu.core.resource import MetaResource

logging.basicConfig(stream=sys.stdout,level=logging.DEBUG)

logger = logging.getLogger("runner")

class LoaderError(Exception):
    pass

class RunContext:

    def __init__(self, opts):
        logger.debug("Invoked with ypath: %r" % opts.ypath)
        logger.debug("Environment YAYBUPATH: %r" % os.environ.get("YAYBUPATH", ""))
        self.ypath = opts.ypath
        if "YAYBUPATH" in os.environ:
            for term in os.environ["YAYBUPATH"].split(":"):
                self.ypath.append(term)

    def locate_file(self, filename):
        """ Locates a file by referring to the defined yaybu path. If the
        filename starts with a / then it is absolutely rooted in the
        filesystem and will be returned unmolested. """
        if filename.startswith("/"):
            return filename
        for prefix in self.ypath:
            candidate = os.path.realpath(os.path.join(prefix, filename))
            logger.debug("Testing for existence of %r" % (candidate,))
            if os.path.exists(candidate):
                return candidate
            logger.debug("%r does not exist" % candidate)
        raise ValueError("Cannot locate file %r" % filename)

class Runner(object):

    def __init__(self, registry=None):
        self.resources = []
        self.registry = registry or MetaResource.resources

    def create_resource(self, typename, instance):
        kls = self.registry[typename](**instance)
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
        parser.add_option("-p", "--ypath", default=[], action="append")
        opts, args = parser.parse_args()
        ctx = RunContext(opts)

        config = yay.load_uri(args[0])

        self.create_resources(config.get("resources", []))
        self.bind_resources()

        shell = Shell(ctx, simulate=opts.simulate)

        for resource in self.resources:
            provider = resource.select_provider()
            provider.apply(shell, )

        return 0


def main():
    return Runner().run()

