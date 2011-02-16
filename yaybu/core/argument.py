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

import dateutil.parser
import urlparse
import os
from abc import ABCMeta, abstractmethod, abstractproperty
from yaybu import recipe

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

class String(Argument):
    def __set__(self, instance, value):
        if value is None:
            pass
        elif not isinstance(value, unicode):
            value = unicode(value, 'utf-8')
        setattr(instance, self.arg_id, value)

class Integer(Argument):

    def __set__(self, instance, value):
        setattr(instance, self.arg_id, int(value))

class DateTime(Argument):

    def __set__(self, instance, value):
        setattr(instance, self.arg_id, dateutil.parser.parse(value))

class Octal(Argument):

    def __set__(self, instance, value):
        if not isinstance(value, int):
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
        if scheme == "file":
            self._file(instance, path)
        elif scheme == "package":
            self._package(instance, netloc, path)
        elif scheme == "recipe":
            self._recipe(instance, netloc, path)
        else:
            raise NotImplementedError('Scheme %s on %s' % (scheme, instance))
