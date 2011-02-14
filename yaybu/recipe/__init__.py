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

import os
from yaybu import util
import yaml # will be yay
import logging

logger = logging.getLogger("cookbook")

class Recipe(object):

    def __init__(self, pathname, data):
        self.pathname = pathname
        self.data = data

    def get_resource(self, filename):
        """ Recipes can have resource files associated with them. These are
        stored in the same directory as the recipe yay file. """
        if filename.startswith("/"):
            filename = filename[1:]
        return util.sibpath(self.pathname, filename)

class Cookbook(object):

    def __init__(self):
        self.recipe = {}

    def add_recipe(self, pathname, stream=None):
        """ An optional stream can be passed, in which case the file at
        'pathname' is not inspected at all, useful for tests, etc. """
        if stream is None:
            stream = open(pathname)
        d = yaml.load(stream)
        self.recipe[d['recipe']] = Recipe(pathname, d)

cookbook = Cookbook()

def get_cookbook():
    return cookbook

dirname = os.path.dirname(__file__)

for filename in os.listdir(dirname):
    if filename.endswith(".yay"):
        path = os.path.join(dirname, filename)
        logger.info("Loading recipe %s" % path)
        cookbook.add_recipe(path)
