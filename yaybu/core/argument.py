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

import error
import dateutil.parser
import types
import urlparse
import os
from abc import ABCMeta, abstractmethod, abstractproperty
from yaybu import recipe

# we abuse urlparse for our parsing needs
urlparse.uses_netloc.append("package")
urlparse.uses_netloc.append("recipe")

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


class Boolean(Argument):
    def __set__(self, instance, value):
        if type(value) in types.StringTypes:
            if value.lower() in ("yes", "on", "true"):
                value = True
            else:
                value = False
        else:
            value = bool(value)
        setattr(instance, self.arg_id, value)

class String(Argument):
    def __set__(self, instance, value):
        if value is None:
            pass
        elif not isinstance(value, unicode):
            value = unicode(value, 'utf-8')
        setattr(instance, self.arg_id, value)

class Integer(Argument):

    def __set__(self, instance, value):
        if not isinstance(value, int):
            value = int(value)
        setattr(instance, self.arg_id, value)

class DateTime(Argument):

    def __set__(self, instance, value):
        if isinstance(value, basestring):
            value = dateutil.parser.parse(value)
        setattr(instance, self.arg_id, value)

class Octal(Argument):

    def __set__(self, instance, value):
        if isinstance(value, int):
            # we assume this is due to lame magic in yaml and rebase it
            value = int(str(value), 8)
        else:
            value = int(value, 8)
        setattr(instance, self.arg_id, value)

class Dict(Argument):
    def __set__(self, instance, value):
        setattr(instance, self.arg_id, value)

class List(Argument):
    def __set__(self, instance, value):
        setattr(instance, self.arg_id, value)

class File(Argument):

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
        if scheme == "file" or not scheme:
            self._file(instance, path)
        elif scheme == "package":
            self._package(instance, netloc, path)
        elif scheme == "recipe":
            self._recipe(instance, netloc, path)
        else:
            raise NotImplementedError('Scheme %s on %s' % (scheme, instance))

class StandardPolicy:

    def __init__(self, policy_name):
        self.policy_name = policy_name

class PolicyTrigger:

    def __init__(self, policy, when, on, immediately=True):
        self.policy = policy
        self.when = when
        self.on = on
        self.immediately = immediately

    def bind(self, resources, target):
        if self.on in resources:
            resources[self.on].register_observer(self.when, target, self.policy, self.immediately)
        else:
            raise error.BindingError("Cannot bind %r to missing resource named '%s'" % (target, self.on))
        return resources[self.on]

class PolicyCollection:

    def __init__(self, standard=None, triggers=()):
        self.standard = standard
        self.triggers = triggers

class PolicyStructure(Argument):

    def __set__(self, instance, value):
        """ Set either a default policy or a set of triggers on the policy collection """
        if type(value) in types.StringTypes:
            coll = PolicyCollection(StandardPolicy(value))
        else:
            triggers = []
            for policy, conditions in value.items():
                if not isinstance(conditions, list):
                    conditions = [conditions]
                for condition in conditions:
                    triggers.append(
                        PolicyTrigger(
                            policy=policy,
                            when=condition['when'],
                            on=condition['on'],
                            immediately=condition.get('immediately', 'true') == 'true')
                        )
            coll = PolicyCollection(triggers=triggers)
        setattr(instance, self.arg_id, coll)
