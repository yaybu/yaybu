# Copyright 2011-2013 Isotoma Limited
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
import datetime
import dateutil.parser
import types
import urlparse
import sys
import unicodedata
import random
from yay import errors, ast


def get_unicode_glyphs():
    return ''.join(
        unichr(char)
        for char in xrange(sys.maxunicode+1)
        if unicodedata.category(unichr(char))[0] in ('LMNPSZ')
        )


# we abuse urlparse for our parsing needs
urlparse.uses_netloc.append("package")


class Property(object):

    def __init__(self, klass, **kwargs):
        self.klass = klass
        self.kwargs = kwargs
        self.__doc__ = kwargs.pop("help", None)


class Argument(ast.Pythonic, ast.Scalarish, ast.AST):

    """
    Adds a property descriptor to a class that automatically validates and
    resolves members of a yay AST node.

    It is immutable.
    """

    def __init__(self, resource, node, **kwargs):
        super(Argument, self).__init__()
        self.resource = resource
        self.node = node
        self.anchor = node.inner.anchor
        self.parent = node.inner
        self.default = kwargs.pop("default", '')
        self.__doc__ = kwargs.pop("help", None)

    def resolve(self):
        try:
            return self.node.resolve()
        except errors.NoMatching:
            return self.default

    def get_labels(self):
        return self.node.get_labels()

    def get_local_labels(self):
        return self.node.get_local_labels()

    def as_safe_string(self):
        return self.node.as_safe_string()

    def contains_secrets(self):
        return self.node.contains_secrets()


class Boolean(Argument):

    """ Represents a boolean. "1", "yes", "on" and "true" are all considered
    to be True boolean values. Anything else is False. """

    default = False

    def resolve(self):
        try:
            value = self.node.resolve()
        except errors.NoMatching:
            return self.default

        if type(value) in types.StringTypes:
           if value.lower() in ("1", "yes", "on", "true"):
                return True
           return False

        return bool(value)


class String(Argument):

    """ Represents a string. """

    def resolve(self):
        return self.node.as_string(default=self.default)

    @classmethod
    def _generate_valid(self):
        l = []
        for i in range(random.randint(0, 1024)):
            l.append(random.choice(get_unicode_glyphs()))
        return "".join(l)


class FullPath(Argument):

    """ Represents a full path on the filesystem. This should start with a
    '/'. """

    def resolve(self):
        value = self.node.as_string(default=self.default)
        #if not value.startswith("/"):
        #    raise error.ParseError("%s is not a full path" % value)
        return value

    @classmethod
    def _generate_valid(self):
        # TODO: needs work
        l = []
        for i in range(random.randint(0, 1024)):
            l.append(random.choice(get_unicode_glyphs()))
        return "/" + "".join(l)


class Integer(Argument):

    """ Represents an integer argument taken from the source file. This can
    throw an :py:exc:error.ParseError if the passed in value cannot represent
    a base-10 integer. """

    def resolve(self):
        return self.node.as_int(default=self.default)

    @classmethod
    def _generate_valid(self):
        return random.randint(0,sys.maxint)


class DateTime(Argument):

    """ Represents a date and time. This is parsed in ISO8601 format. """

    def resolve(self):
        value = self.node.as_string(default=self.default)
        if not value:
            return None
        if isinstance(value, basestring):
            return dateutil.parser.parse(value)

    @classmethod
    def _generate_valid(self):
        return datetime.datetime.fromtimestamp(random.randint(0, sys.maxint))


class Octal(Integer):

    """ An octal integer.  This is specifically used for file permission modes. """

    def resolve(self):
        try:
            value = self.node.resolve()
        except errors.NoMatching:
            value = self.default
        if isinstance(value, int):
            # we assume this is due to lame magic in yaml and rebase it
            return int(str(value), 8)
        return int(value, 8)

    @classmethod
    def _generate_valid(self):
        return random.choice([0755, 0644, 0777])


class Dict(Argument):

    def resolve(self):
        return self.node.as_dict(default=self.default)

    @classmethod
    def _generate_valid(self):
        return {}


class List(Argument):

    def resolve(self):
        return self.node.as_list(default=self.default)

    def get_iterable(self, default=object()):
        return self.node.get_iterable()

    def __iter__(self):
        return iter(self.node.resolve())

    @classmethod
    def _generate_valid(self):
        return []


class File(Argument):

    """ Provided with a URL, this can get files by various means. Often used
    with the package:// scheme """

    pass


class StandardPolicy:

    def __init__(self, policy_name):
        self.policy_name = policy_name


class PolicyTrigger:

    def __init__(self, policy, when, on):
        self.policy = policy
        self.when = when
        self.on = on

    def bind(self, resources, target):
        if not self.on in resources:
            raise error.BindingError("Cannot bind %r to missing resource named '%s'" % (target, self.on))
        if not self.when in resources[self.on].policies:
            raise error.BindingError("%r cannot bind to non-existant event %s on resource %r" % (target, self.when, resources[self.on]))
        resources[self.on].register_observer(self.when, target, self.policy)
        return resources[self.on]


class PolicyCollection:

    """ A collection of policy structures. """

    literal = None
    """ The policy that is set as the "standard" policy, not one that depends on a trigger. """

    triggers = ()
    """ A list of PolicyTrigger objects that represent optional triggered policies. """

    def __init__(self, literal=None, triggers=()):
        self.literal = literal
        self.triggers = triggers

    def literal_policy(self, resource):
        if self.literal is not None:
            return resource.policies[self.literal.policy_name]
        else:
            import policy
            return policy.NullPolicy

    def all_potential_policies(self, resource):
        if self.literal:
            yield resource.policies[self.literal.policy_name]
        else:
            for pol in set(t.policy for t in self.triggers):
                yield resource.policies[pol]


class PolicyArgument(Argument):

    """ Parses the policy: argument for resources, including triggers etc. """

    def resolve(self):
        instance = self.resource

        try:
            value = self.node.resolve()
        except errors.NoMatching:
            #return PolicyCollection(instance.policies.default())
            return None

        if type(value) in types.StringTypes:
            if not value in instance.policies:
                raise error.ParseError("'%s' is not a valid policy for %r" % (value, instance))
            return PolicyCollection(StandardPolicy(value))

        if isinstance(value, dict):
            triggers = []
            for policy, conditions in value.items():
                if not policy in instance.policies:
                    raise error.ParseError("'%s' is not a valid policy for %r" % (policy, instance))
                if not isinstance(conditions, list):
                    conditions = [conditions]
                for condition in conditions:
                    triggers.append(
                        PolicyTrigger(
                            policy=policy,
                            when=str(condition['when']),
                            on=str(condition['on']),
                            )
                        )
            return PolicyCollection(triggers=triggers)

        raise error.ParseError("Expected either a string literal or mapping as 'policy' argument for %r" % instance)

