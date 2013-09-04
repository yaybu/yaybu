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

import os
import sys
import inspect
import itertools
from yay import errors


# merci, twisted
def sibpath(path, sibling):
    """Return the path to a sibling of a file in the filesystem.

    This is useful in conjunction with the special __file__ attribute
    that Python provides for modules, so modules can load associated
    resource files.
    """
    return os.path.join(os.path.dirname(os.path.abspath(path)), sibling)


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

