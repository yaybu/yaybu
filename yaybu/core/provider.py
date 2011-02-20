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

""" Core classes for providers """

from abc import ABCMeta, abstractmethod, abstractproperty

import policy

class ProviderType(ABCMeta):

    """ Registers the provider with the resource which it provides """

    def __new__(meta, class_name, bases, new_attrs):
        cls = super(ProviderType, meta).__new__(meta, class_name, bases, new_attrs)
        for policy in cls.policies:
            policy.providers.append(cls)
        return cls


class Provider(object):
    __metaclass__ = ProviderType

    # every provider should have a name
    name = None
    # in your class, specify which policies you provide an implementation for
    # these policies should all be for the same resource
    policies = []

    def __init__(self, resource):
        self.resource = resource

    @classmethod
    def isvalid(self, policy, resource, yay):
        """ Returns True if this provider is valid for the specified resource,
        within the context of the provided yay structure. This returns True by
        default. If you want your provider to be more discriminating, then
        make it so. In particular if you want two providers for a policy, then
        only one of those providers may return True from this method. """
        return True

    @abstractmethod
    def apply(self, shell):
        """ Execute this provider using the supplied shell object. This base
        method must be overridden. This should return True if the provider
        changed anything, or False if it did not need to change anything (i.e.
        the Resource was already in the state the policy ensures). """
        return False

class NullProvider(Provider):
    policies = [policy.NullPolicy]

    def apply(self, shell):
        pass
