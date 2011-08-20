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

"""
This module provides support functions for people wanting to use Yaybu
without Yay. This functionality is EXPERIMENTAL.
"""

import sys, inspect
from yaybu.core import resource

__bundle = None

def get_bundle():
    global __bundle
    if not __bundle:
        __bundle = resource.ResourceBundle()
    return __bundle

def reset_bundle():
    global __bundle
    __bundle = None

def create_wrapper(resource_type):
    """
    This creates a function for a Resource that performs string substitution
    and registers the  resource with a bundle.
    """
    def create_resource(**kwargs):
        caller = inspect.currentframe().f_back

        # Mutate kwargs based on local variables
        for k, v in kwargs.items():
            if isinstance(v, basestring):
                kwargs[k] = v.format(**caller.f_locals)

        # Create a Resource and add it to the bundle
        get_bundle().create(resource_type, kwargs)

    return create_resource

def register_resources():
    """
    This iterates over all known Resource Types and creates a proxy
    for them. The proxy will automatically format any strings it is passed
    with all variables in the local context. The proxy automatically
    registers the Resource with a resource bundle.

    It is called automatically when this module is imported.
    """
    module = sys.modules[__name__]
    for resource_type in resource.ResourceType.resources.keys():
        setattr(module, resource_type, create_wrapper(resource_type))

register_resources()

