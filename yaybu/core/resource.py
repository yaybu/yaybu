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

from argument import Argument, List, PolicyStructure, String
from yaybu import recipe
import collections

class NoValidPolicy(Exception):
    pass

class NonConformingPolicy(Exception):
    pass

class NoSuitableProviders(Exception):
    pass

class TooManyProviders(Exception):
    pass

class ResourceType(type):

    resources = {}

    def __new__(meta, class_name, bases, new_attrs):
        cls = type.__new__(meta, class_name, bases, new_attrs)
        cls.__args__ = []
        for b in bases:
            if hasattr(b, "__args__"):
                cls.__args__.extend(b.__args__)
        cls.policies = {}
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

    __metaclass__ = ResourceType

    # The arguments for this resource, set in the metaclass
    __args__ = []
    # the policies for this resource, registered as policies are created
    policies = {}
    # the list of policies provided by configuration
    policy = PolicyStructure()
    name = String()

    def __init__(self, **kwargs):
        """ Pass a dictionary of arguments and they will be updated from the
        supplied data. A special argument 'yay' should be passed that contains
        the entire yay structure, used in provider selection. """
        self.yay = kwargs.pop("yay", None)
        for key, value in kwargs.items():
            if not key in self.__args__:
                raise AttributeError("Cannot assign argument '%s' to resource %s" % (key, self))
            setattr(self, key, value)
        self.observers = collections.defaultdict(list)

    def register_observer(self, when, resource, policy, immediately):
        self.observers[when].append((immediately, resource, policy))

    def validate(self):
        """ Given the provided yay configuration dictionary, validate that
        this resource is correctly specified. Will raise an exception if it is
        invalid. Returns the provider if it is valid.

        We only validate if:

           - the chosen policies all exist, or
           - there is at least one default policy, and
           - the arguments provided conform with all selected policies, and
           - the selected policies all share a single provider

        If the above is all true then we can identify a provider that should
        be able to implement the required policies.

        """
        policy = self.select_policy()
        providers = set()
        if not policy:
            # No defined policies means this resource cannot be implemented
            raise NoValidPolicy(self)
        if not policy.conforms(self):
                # if any of the chosen policies does not conform, that's an error
            raise NonConformingPolicy(policy.name)
        providers.update(policy.providers)
        if len(providers) == 0:
            raise NoSuitableProviders(self)
        elif len(providers) == 1:
            return providers.pop()
        else:
            raise TooManyProviders(self)

    def bind(self, resources):
        if self.policy is not None:
            for trigger in self.policy.triggers:
                trigger.bind(resources, self)

    def select_policy(self):
        """ Return the list of policies that are selected for this resource. """
        if self.policy is not None:
            return self.policies[self.policy.standard.policy_name]
        else:
            for p in self.policies.values():
                if p.default is True:
                    return p

    def select_provider(self):
        """ Right now a side effect of validation is determining the provider.
        """
        provider = self.validate()
        return provider(self, None)

    def dict_args(self):

        """ Return all argument names and values in a dictionary. If an
        argument has no default and has not been set, it's value in the
        dictionary will be None. """

        d = {}
        for a in self.__args__:
            d[a] = getattr(self, a, None)
        return d

    def __repr__(self):
        classname = getattr(self, '__resource_name__', self.__class__.__name__)
        return "%s[%s]" % (classname, self.name)

