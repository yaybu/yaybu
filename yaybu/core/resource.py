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

from argument import Argument
from yaybu import recipe

class NoValidProvider(Exception):
    pass

class TooManyProviders(Exception):
    pass

class MetaResource(type):

    resources = {}

    def __new__(meta, class_name, bases, new_attrs):
        cls = type.__new__(meta, class_name, bases, new_attrs)
        cls.__args__ = []
        cls.providers = []
        cls.policies = []
        if class_name != 'Resource':
            rname = new_attrs.get("__resource_name__", class_name)
            if rname in meta.resources:
                raise ValueError("Redefinition of resource %s" % rname)
            else:
                meta.resources[rname] = cls
        for key, value in new_attrs.items():
            if isinstance(value, Argument):
                cls.__args__.append(key)
        return cls

class Resource(object):

    """ A resource represents a resource that can be configured on the system.
    This might be as simple as a symlink or as complex as a database schema
    migration. Resources have policies that represent how the resource is to
    be treated. Providers are the implementation of the resource policy.

    Resource definitions specify the complete set of attributes that can be
    configured for a resource. Policies define which attributes must be
    configured for the policy to be used.

    """

    __metaclass__ = MetaResource

    def __init__(self, **kwargs):
        """ Pass a dictionary of arguments and they will be updated from the supplied data """
        for key, value in kwargs.items():
            if not hasattr(self, key):
                raise AttributeError("Cannot assign argument '%s' to resource" % key)
            setattr(self, key, value)

    def select_provider(self, yay):
        valid = [p for p in self.providers if p.isvalid(self, yay)]
        if not valid:
            raise NoValidProvider()
        if len(valid) == 1:
            return valid[0](self, yay)
        else:
            raise TooManyProviders()

    def dict_args(self):

        """ Return all argument names and values in a dictionary. If an
        argument has no default and has not been set, it's value in the
        dictionary will be None. """

        d = {}
        for a in self.__args__:
            d[a] = getattr(self, a, None)
        return d
