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

import sys, os, hashlib
from yaybu.core.argument import Argument, List, PolicyArgument, String
from yaybu.core import policy
from yaybu import error
import collections
from yaybu.core import ordereddict
from yaybu.core import event

from yay import errors
from yay.ast import PythonicWrapper
from yay.errors import LanguageError, get_exception_context

class ResourceType(type):

    """ Keeps a registry of resources as they are created, and provides some
    simple access to their arguments. """

    resources = {}

    def __new__(meta, class_name, bases, new_attrs):
        cls = type.__new__(meta, class_name, bases, {})

	# Ultimately do this like Django and have a contribute_to_class, i
	# think
        for k, v in new_attrs.items():
            if isinstance(v, Argument):
                v.name = k #.replace("_", "-")
            setattr(cls, k, v)

        cls.policies = AvailableResourcePolicies()

        if class_name != 'Resource':
            rname = new_attrs.get("__resource_name__", class_name)
            if rname in meta.resources:
                raise error.ParseError("Redefinition of resource %s" % rname)
            else:
                meta.resources[rname] = cls

        return cls

    @classmethod
    def clear(self):
        self.resources = {}

class AvailableResourcePolicies(dict):

    """ A collection of the policies available for a resource, with some logic
    to work out which of them is the one and only default policy. """

    def default(self):
        default = [p for p in self.values() if p.default]
        if default:
            return default[0]
        else:
            return policy.NullPolicy


class Resource(object):

    """ A resource represents a resource that can be configured on the system.
    This might be as simple as a symlink or as complex as a database schema
    migration. Resources have policies that represent how the resource is to
    be treated. Providers are the implementation of the resource policy.

    Resource definitions specify the complete set of attributes that can be
    configured for a resource. Policies define which attributes must be
    configured for the policy to be used.

    """

    __metaclass__ = ResourceType

    policies = AvailableResourcePolicies()
    """ A dictionary of policy names mapped to policy classes (not objects).

    These are the policies for this resource class.

    Here be metaprogramming magic.

    Dynamically allocated as Yaybu starts up this is effectively static once
    we're up and running. The combination of this attribute and the policy
    argument below is sufficient to determine which provider might be
    appropriate for this resource.

    """

    policy = PolicyArgument()
    """ The list of policies provided by configuration. This is an argument
    like any other, but has a complex representation that holds the conditions
    and options for the policies as specified in the input file. """

    name = String()

    watch = List(default=[])
    """ A list of files to monitor while this resource is applied

    The file will be hashed before and after a resource is applied.
    If the hash changes, then it will be like a policy has been applied
    on that file.

    For example::

        resources.append:
          - Execute:
              name: buildout-foobar
              command: buildout2.6
              watch:
                - /var/local/sites/foobar/apache/apache.cfg

          - Service:
              name: apache2
              policy:
                restart:
                  when: watched
                  on: File[/var/local/sites/foobar/apache/apache.cfg]
    """

    def __init__(self, inner):
        """ Takes a reference to a Yay AST node """
        self.inner = PythonicWrapper(inner)
        self.observers = collections.defaultdict(list)

    @classmethod
    def get_argument_names(klass):
        for k in dir(klass):
            attr = getattr(klass, k)
            if isinstance(attr, Argument):
                yield attr.name

    def get_argument_values(self):
        """ Return all argument names and values in a dictionary. If an
        argument has no default and has not been set, it's value in the
        dictionary will be None. """

        retval = {}
        for key in self.get_argument_names():
            retval[key] = getattr(self, key, None)

    def register_observer(self, when, resource, policy, immediately):
        self.observers[when].append((immediately, resource, policy))

    def validate(self):
        """ Validate that this resource is correctly specified. Will raise
        an exception if it is invalid. Returns True if it is valid.

        We only validate if:

           - only known arguments are specified
           - the chosen policies all exist, or
           - there is at least one default policy, and
           - the arguments provided conform with all selected policies, and
           - the selected policies all share a single provider

        If the above is all true then we can identify a provider that should
        be able to implement the required policies.

        """

        # This will throw any error if any of our validation fails
        self.get_argument_values()

        # Only allow keys that are in the schema
        for key in self.inner.keys():
            if not key in self.get_argument_names():
                raise error.ParseError("'%s' is not a valid option for resource %s" % (key, self))

        # Error if doesn't conform to policy
        this_policy = self.get_default_policy()
        if not this_policy.conforms(self):
            raise error.NonConformingPolicy(this_policy.name)

        # throws an exception if there is not oneandonlyone provider
        provider = this_policy.get_provider(self)
        return True

    def apply(self, context, yay=None, policy=None):
        """ Apply the provider for the selected policy, and then fire any
        events that are being observed. """
        if yay is None:
            yay = {}
        if policy is None:
            pol = self.get_default_policy()
        else:
            pol_class = self.policies[policy]
            pol = pol_class(self)
        prov_class = pol.get_provider(yay)
        prov = prov_class(self)
        changed = prov.apply(context)
        event.state.clear_override(self)
        if changed:
            self.fire_event(pol.name)
        return changed

    def fire_event(self, name):
        """ Apply the appropriate policies on the resources that are observing
        this resource for the firing of a policy. """
        for immediately, resource, policy in  self.observers[name]:
            if immediately is False:
                raise NotImplementedError
            event.state.override(resource, policy)

    def bind(self, resources):
        """ Bind this resource to all the resources on which it triggers.
        Returns a list of the resources to which we are bound. """
        bound = []
        if self.policy is not None:
            for trigger in self.policy.triggers:
                bound.append(trigger.bind(resources, self))
        return bound

    def get_default_policy(self):
        """ Return an instantiated policy for this resource. """
        return event.state.policy(self)

    @property
    def id(self):
        classname = getattr(self, '__resource_name__', self.__class__.__name__)
        return "%s[%s]" % (classname, self.inner.name.as_string())

    def __repr__(self):
        return self.id

    def __unicode__(self):
        classname = getattr(self, '__resource_name__', self.__class__.__name__)
        return u"%s[%s]" % (classname, self.inner.name.as_string())


class ResourceBundle(ordereddict.OrderedDict):

    """ An ordered, indexed collection of resources. Pass in a specification
    that consists of scalars, lists and dictionaries and this class will
    instantiate the appropriate resources into the structure. """

    @classmethod
    def create_from_list(cls, specification):
        """ Given a list of types and parameters, build a resource bundle """
        from yay.ast import bind
        nodes = bind(specification)
        return self.create_from_yay_expression(nodes)

    @classmethod
    def create_from_yay_expression(cls, expression, verbose_errors=False):
        """ Given a Yay expression that resolves to a list of types and
        parameters, build a resource bundle.  """
        bundle = cls()
        try:
            for node in expression.get_iterable():
                bundle.add_from_node(node)

        except LanguageError as exc:
            p = error.ParseError()
            p.msg = str(exc)
            if verbose_errors:
                p.msg += "\n" + get_exception_context()
            if exc.anchor:
                p.file = exc.anchor.source
                p.line = exc.anchor.lineno
            p.column = 0
            raise p

        except error.ParseError as exc:
            if getattr(node, "anchor", None):
                exc.msg += "\nFile %s, line %d, column %s" % (node.anchor.source, node.anchor.lineno, "unknown")
                exc.file = node.anchor.source
                exc.line = node.anchor.lineno
            exc.column = 0
            raise

        return bundle

    def key_remap(self, kw):
        """ Maps - to _ to make resource attribute name more pleasant. """
        for k, v in kw.items():
            k = k.replace("-", "_")
            yield str(k),v

    def add_from_node(self, spec):
        try:
            spec.as_dict()
        except errors.TypeError:
            raise error.ParseError("Not a valid Resource definition")

        keys = list(spec.keys())
        if len(keys) > 1:
            raise error.ParseError("Too many keys in list item")

        typename = keys[0]
        instances = spec.get_key(typename)

        try:
            instances.as_dict()
            iterable = [instances]
        except errors.TypeError:
            iterable = instances.get_iterable()

        for instance in iterable:
            self.add(typename, instance)

    def add(self, typename, instance):
        if not hasattr(instance, "keys"):
            raise error.ParseError("Expected mapping for %s" % typename)

        try:
            kls = ResourceType.resources[typename]
        except KeyError:
            raise error.ParseError("There is no resource type of '%s'" % typename)

        resource = kls(instance)
        if resource.id in self:
            raise error.ParseError("'%s' cannot be defined multiple times" % resource.id)

        resource.validate()

        self[resource.id] = resource

        # Create implicit File[] nodes for any watched files
        for watched in resource.watch:
            w = self.create("File", {
                "name": watched.as_string(),
                "policy": "watched",
            })
            w._original_hash = None

        return resource

    def bind(self):
        """ Bind all the resources so they can observe each others for policy
        triggers. """
        for i, resource in enumerate(self.values()):
            for bound in resource.bind(self):
                if bound == resource:
                    raise error.BindingError("Attempt to bind %r to itself!" % resource)
                j = self.values().index(bound)
                if j > i:
                    raise error.BindingError("Attempt to bind forwards on %r" % resource)

    def apply(self, ctx, config):
        """ Apply the resources to the system, using the provided context and
        overall configuration. """
        for resource in self.values():
           if hasattr(resource, "_original_hash"):
               resource._original_hash = resource.hash(ctx)

        something_changed = False
        for resource in self.values():
            with ctx.changelog.resource(resource):
                if resource.apply(ctx, config):
                    something_changed = True
        return something_changed
