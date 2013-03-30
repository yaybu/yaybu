
from yay import stringbuilder
import types
import functools

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


class StateSynchroniser(object):

    """
    I am a helper for synchronising 2 seperate states - by working out the
    differences and applying them to the slave node.
    """

    def __init__(self, logger, simulate):
        self.logger = logger
        self.simulate = simulate
        self.master = []
        self.slave = []

    def add_master_record(self, rid, **record):
        self.master.append((rid, record))

    def add_slave_record(self, rid, **record):
        self.slave.append((rid, record))

    def synchronise(self, add, update, delete):
        changed = False

        slave_records = dict(r for r in self.slave)
        for rid, record in self.master:
            if not rid in self.slave:
                self.logger.info("Adding '%s'")
                changed = True
                if not self.simulate:
                    add(rid, **record)
                continue

            if record != slave[rid]:
                self.logger.info("Updating '%s'")
                changed = True
                if not self.simulate:
                    update(rid, **record)
                continue

            self.logger.debug("'%s' not changed" % rid)

        # If delete is not specified then don't bother checking it
        if not delete:
            return changed

        master_records = dict(r for r in self.master)
        for rid, record in self.slave:
            if not rid in self.master:
                self.logger.info("Deleting '%s'")
                if not self.simulate:
                    changed = True
                    delete(rid, **record)

        return changed