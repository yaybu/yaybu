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

    def __init__(self, resource, yay):
        self.resource = resource
        self.yay = yay

    @classmethod
    @abstractmethod
    def isvalid(self, resource, yay):
        """ Returns True if this provider is valid for the specified resource,
        within the context of the provided yay structure. This will return
        True, unless a provider is specified. If a provider is specified then
        the name specified must match the name of this provider. """
        if hasattr(resource, 'provider'):
            if resource.provider == self.name:
                return True
            if resource.provider is not None:
                return False
        return True

class NullProvider(Provider):
    policies = [policy.NullPolicy]