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

import abstract
import dateutil.parser
import urlparse
import os
from yaybu import recipe

try:
    import wingdbstub
except ImportError:
    pass


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
        if class_name != 'Resource':
            rname = new_attrs.get("__resource_name__", class_name)
            if rname in meta.resources:
                raise ValueError("Redefinition of resource %s" % rname)
            else:
                meta.resources[rname] = cls
        for key, value in new_attrs.items():
            if isinstance(value, abstract.Argument):
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

class Policy(object):

    """
    A policy is a representation of a resource. A policy requires a
    certain argument signature to be present before it can be used. There may
    be multiple policies selected for a resource, in which case all argument
    signatures must be conformant.

    Providers must provide all selected policies to be a valid provider for
    the resource.
    """

    signature = () # Override this with a list of assertions


    def __init__(self, name):
        self.name = name

    @classmethod
    def conforms(self, resource):
        """ Test if the provided resource conforms to the signature for this
        policy. """
        for a in self.signature:
            if not a.test(resource):
                return False
        return True

class ArgumentAssertion(object):

    """ An assertion of the state of an argument """

    def __init__(self, name):
        self.name = name

class Present(ArgumentAssertion):

    """ The argument has been specified, or has a default value. """

    def test(self, resource):
        """ Test that the argument this asserts for is present in the
        resource. """
        if getattr(resource, self.name) is not None:
            return True
        return False

class Absent(ArgumentAssertion):

    """ The argument has not been specified by the user and has no default
    value. An argument with a default value is always defined. """

    def test(self, resource):
        if getattr(resource, self.name) is None:
            return True
        return False

class XOR(ArgumentAssertion):

    def __init__(self, *args):
        self.args = args

    def test(self, resource):
        l = [1 for a in self.args if a.test(resource)]
        if len(l) == 0:
            return False
        elif len(l) == 1:
            return True
        else:
            return False

class String(abstract.Argument):
    def __set__(self, instance, value):
        if value is None:
            pass
        elif not isinstance(value, unicode):
            value = unicode(value, 'utf-8')
        setattr(instance, self.arg_id, value)

class Integer(abstract.Argument):

    def __set__(self, instance, value):
        setattr(instance, self.arg_id, int(value))

class DateTime(abstract.Argument):

    def __set__(self, instance, value):
        setattr(instance, self.arg_id, dateutil.parser.parse(value))

class Octal(abstract.Argument):

    def __set__(self, instance, value):
        setattr(instance, self.arg_id, int(value, 8))

class Dict(abstract.Argument):
    def __set__(self, instance, value):
        setattr(instance, self.arg_id, value)

class File(abstract.Argument):

    """ Provided with a URL, this can get files by various means. Often used
    with the package:// scheme """

    def _file(self, instance, path):
        # should really be some kind of proxy object
        setattr(instance, self.arg_id, path)

    def _package(self, instance, netloc, subpath):
        module = __import__(netloc, {}, {}, [""])
        module_path = module.__path__[0]
        path = os.path.join(module_path, subpath[1:])
        # should really be some kind of proxy object
        setattr(instance, self.arg_id, path)

    def _recipe(self, instance, netloc, subpath):
        cookbook = recipe.get_cookbook()
        r = cookbook.recipe[netloc]
        # should really be some kind of proxy object
        setattr(instance, self.arg_id, r.get_resource(subpath))

    def __set__(self, instance, value):
        (scheme, netloc, path, params, query, fragment) = urlparse.urlparse(value)
        if scheme == "file":
            self._file(instance, path)
        elif scheme == "package":
            self._package(instance, netloc, path)
        elif scheme == "recipe":
            self._recipe(instance, netloc, path)
        else:
            raise NotImplementedError
