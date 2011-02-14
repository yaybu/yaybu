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

""" Abstract Base Classes for yaybu """

from abc import ABCMeta, abstractmethod, abstractproperty

class Provider:
    __metaclass__ = ABCMeta

    # every provider should have a name
    name = None

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

class Argument(object):

    """ Stores the argument value on the instance object. It's a bit fugly,
    neater ways of doing this that do not involve passing extra arguments to
    Argument are welcome. """

    metaclass = ABCMeta
    argument_id = 0

    def __init__(self, default=None):
        self.default = default
        self.arg_id = "argument_%d" % Argument.argument_id
        Argument.argument_id += 1

    def __get__(self, instance, owner):
        if instance is None:
            raise AttributeError
        if hasattr(instance, self.arg_id):
            return getattr(instance, self.arg_id)
        else:
            return self.default

    @abstractmethod
    def __set__(self, instance, value):
        """ Set the property. The value will be a UTF-8 encoded string read from the yaml source file. """

