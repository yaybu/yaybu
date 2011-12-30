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
from argument import Argument, List, PolicyArgument, String
import policy
import error
import collections
import ordereddict
import event

class ResourceType(type):

    """ Keeps a registry of resources as they are created, and provides some
    simple access to their arguments. """

    resources = {}

    def __new__(meta, class_name, bases, new_attrs):
        cls = type.__new__(meta, class_name, bases, new_attrs)
        cls.__args__ = []
        for b in bases:
            if hasattr(b, "__args__"):
                cls.__args__.extend(b.__args__)
        cls.policies = AvailableResourcePolicies()
        if class_name != 'Resource':
            rname = new_attrs.get("__resource_name__", class_name)
            if rname in meta.resources:
                raise error.ParseError("Redefinition of resource %s" % rname)
            else:
                meta.resources[rname] = cls
        for key, value in new_attrs.items():
            if isinstance(value, Argument):
                cls.__args__.append(key)
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

    # The arguments for this resource, set in the metaclass
    __args__ = []

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

    watch = List()
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

    def __init__(self, **kwargs):
        """ Pass a dictionary of arguments and they will be updated from the
        supplied data. """
        setattr(self, "name", kwargs["name"])
        for key, value in kwargs.items():
            if not key in self.__args__:
                raise AttributeError("Cannot assign argument '%s' to resource %s" % (key, self))
            setattr(self, key, value)
        self.observers = collections.defaultdict(list)

    def register_observer(self, when, resource, policy, immediately):
        self.observers[when].append((immediately, resource, policy))

    def validate(self, yay=None):
        """ Given the provided yay configuration dictionary, validate that
        this resource is correctly specified. Will raise an exception if it is
        invalid. Returns the provider if it is valid.

        We only validate if:

           - the chosen policies all exist, or
           - there is at least one default policy, and
           - the arguments provided conform with all selected policies, and
           - the selected policies all share a single provider

        If the above is all true then we can identify a provider that should
        be able to implement the required policies.

        """
        if yay is None:
            yay = {}
        this_policy = self.get_default_policy()
        if not this_policy.conforms(self):
            raise error.NonConformingPolicy(this_policy.name)
        # throws an exception if there is not oneandonlyone provider
        provider = this_policy.get_provider(self, yay)
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

    def dict_args(self):

        """ Return all argument names and values in a dictionary. If an
        argument has no default and has not been set, it's value in the
        dictionary will be None. """

        d = {}
        for a in self.__args__:
            d[a] = getattr(self, a, None)
        return d

    @property
    def id(self):
        classname = getattr(self, '__resource_name__', self.__class__.__name__)
        return "%s[%s]" % (classname, self.name.encode("utf-8"))

    def __repr__(self):
        return self.id

    def __unicode__(self):
        classname = getattr(self, '__resource_name__', self.__class__.__name__)
        return u"%s[%s]" % (classname, self.name)


class ResourceBundle(ordereddict.OrderedDict):

    """ An ordered, indexed collection of resources. Pass in a specification
    that consists of scalars, lists and dictionaries and this class will
    instantiate the appropriate resources into the structure. """

    @classmethod
    def create_from_list(cls, specification):
        """ Given a list of types and parameters, build a resource bundle """
        bundle = cls()
        for spec in specification:
            bundle.add_from_spec(spec)
        return bundle

    @classmethod
    def create_from_yay_expression(cls, expression):
	""" Given a Yay expression that resolves to a list of types and
        parameters, build a resource bundle.  """
        bundle = cls()
        for node in expression:
            spec = node.resolve()
            try:
                bundle.add_from_spec(spec)
            except error.ParseError as exc:
                exc.msg += "\nFile %s, line %d, column %d" % (node.name, node.line, node.column)
                exc.file = node.name
                exc.line = node.line
                exc.column = node.column
                raise

        return bundle

    def key_remap(self, kw):
        """ Maps - to _ to make resource attribute name more pleasant. """
        for k, v in kw.items():
            k = k.replace("-", "_")
            yield str(k),v

    def add_from_spec(self, spec):
        if not hasattr(spec, "keys"):
            raise error.ParseError("Not a valid Resource definition")

        if len(spec.keys()) > 1:
            raise error.ParseError("Too many keys in list item")

        typename, instances = spec.items()[0]
        if not isinstance(instances, list):
            instances = [instances]

        for instance in instances:
            self.add(typename, instance)

    def add(self, typename, instance):
        if not isinstance(instance, dict):
            raise error.ParseError("Expected mapping for %s, got %s" % (typename, instance))

        try:
            kls = ResourceType.resources[typename](**dict(self.key_remap(instance)))
        except KeyError:
            raise error.ParseError("There is no resource type of '%s'" % typename)

        if kls.id in self:
            raise error.ParseError("'%s' cannot be defined multiple times" % kls.id)

        self[kls.id] = kls

        # Create implicit File[] nodes for any watched files
        for watched in instance.get("watch", []):
            w = self.create("File", {
                "name": watched,
                "policy": "watched",
                })
            w._original_hash = w.hash()

        return kls

    # DEPRECATED
    create = add

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
        something_changed = False
        for resource in self.values():
            with ctx.changelog.resource(resource):
                if resource.apply(ctx, config):
                    something_changed = True
        return something_changed

