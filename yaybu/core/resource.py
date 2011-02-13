
import abstract
import dateutil.parser
import urlparse
import os
from yaybu import recipe
import wingdbstub

class NoValidProvider(Exception):
    pass

class TooManyProviders(Exception):
    pass

class MetaResource(type):
    def __new__(meta, class_name, bases, new_attrs):
        cls = type.__new__(meta, class_name, bases, new_attrs)
        cls.__args__ = []
        for key, value in new_attrs.items():
            if isinstance(value, abstract.Argument):
                cls.__args__.append(key)
        return cls

class Resource(object):

    """ Documentation for Resource """

    __metaclass__ = MetaResource

    provider = None

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
        argument has no default and has not been set, we will throw an
        exception. """
        d = {}
        for a in self.__args__:
            d[a] = getattr(self, a)
        return d

class String(abstract.Argument):
    def __set__(self, instance, value):
        setattr(instance, self.arg_id, unicode(value, 'utf-8'))

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
        setattr(instance, self.arg_id, value.copy())

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
