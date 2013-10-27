
import difflib
import inspect
import itertools

from yay import errors

from yaybu import error


_MARKER = object()
_MARKER2 = object()


def args_from_expression(func, expression, ignore=(), kwargs=()):
    if inspect.isclass(func):
        func = getattr(func, "__init__")
    args, varg_name, kwarg_name, defaults = inspect.getargspec(func)

    if args[0] == "self":
        args.pop(0)

    len_args = len(args)
    len_defaults = len(defaults) if defaults else 0
    padding = len_args - len_defaults

    defaults = itertools.chain(itertools.repeat(_MARKER, padding), defaults)

    result = {}
    for arg, default in itertools.chain(zip(args, defaults), zip(kwargs, itertools.repeat(_MARKER2, len(kwargs)))):
        if arg in ignore:
            continue
        try:
            if not expression:
                raise KeyError
            node = expression.get_key(arg)
        except KeyError:
            if default == _MARKER:
                raise errors.NoMatching(arg)
            elif default == _MARKER2:
                continue
            result[arg] = default
        else:
            if default == _MARKER:
                result[arg] = node.resolve()
            elif isinstance(default, int):
                result[arg] = node.as_int()
            elif isinstance(default, basestring):
                result[arg] = node.as_string()
            else:
                result[arg] = node.resolve()

    return result


def get_driver_from_expression(
    expression,
    get_driver,
    provider,
    extra_drivers,
    context,
        ignore=()):
    try:
        driver_id = expression.as_string()
        driver_id_expr = expression
        expression = None
    except errors.TypeError:
        driver_id = expression.id.as_string()
        driver_id_expr = expression.id

    if driver_id in extra_drivers:
        Driver = extra_drivers[driver_id]
    else:
        try:
            Driver = get_driver(getattr(provider, driver_id))
        except AttributeError:
            msg = ["'%s' is not a valid driver" % driver_id]
            all_drivers = list(
                v for v in vars(provider) if not v.startswith("_"))
            all_drivers.extend(extra_drivers.keys())
            all_drivers = sorted(set(all_drivers))
            possible = difflib.get_close_matches(driver_id, all_drivers)
            if possible:
                msg.append("The closest valid drivers are: %s" %
                           "/".join(possible))
            raise error.ValueError(
                '\n'.join(msg), anchor=driver_id_expr.expand().anchor)
    driver = Driver(**args_from_expression(Driver, expression, ignore=ignore))
    driver.yaybu_context = context
    return driver
