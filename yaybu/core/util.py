
from yay import stringbuilder
import types

def version():
    import pkg_resources

    yaybu_version = pkg_resources.get_distribution('Yaybu').version
    yay_version = pkg_resources.get_distribution('Yay').version
    return 'Yaybu %s\n' \
           'yay %s' % (yaybu_version, yay_version)

class memoized(object):
    """
    Decorator. Caches a function's return value each time it is called.
    If called later with the same arguments, the cached value is returned 
    (not reevaluated).
    """
    def __init__(self, func):
        self.func = func
        self.cache = {}
    def __call__(self, *args):
        try:
            return self.cache[args]
        except KeyError:
            value = self.func(*args)
            self.cache[args] = value
            return value
        except TypeError:
            # uncachable -- for instance, passing a list as an argument.
            # Better to not cache than to blow up entirely.
            return self.func(*args)
    def __repr__(self):
        '''Return the function's docstring.'''
        return self.func.__doc__
    def __get__(self, obj, objtype):
        '''Support instance methods.'''
        return functools.partial(self.__call__, obj)

def get_encrypted(val):
    scalar_types = (
        types.StringType,
        types.UnicodeType,
        types.IntType,
        types.BooleanType,
        types.LongType,
        types.NoneType)
    if isinstance(val, stringbuilder.String):
        return val.unprotected
    elif isinstance(val, scalar_types):
        return val
    elif isinstance(val, types.DictionaryType):
        d = {}
        for key, value in val.items():
            d[key] = get_encrypted(value)
        return d
    elif isinstance(val, (types.ListType, types.TupleType)):
        l = []
        for item in val:
            l.append(get_encrypted(item))
        return l
    else:
        raise ValueError("Unable to convert %r" % val)
    
