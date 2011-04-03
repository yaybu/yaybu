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

import sys
from argument import Argument, List, PolicyStructure, String
import policy
import error
from yaybu import recipe
import collections
import ordereddict

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
        cls.policies = {}
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
    # the policies for this resource, registered as policies are created
    policies = {}
    # the list of policies provided by configuration
    policy = PolicyStructure()
    # any policy applied by a policy trigger
    policy_override = None
    name = String()

    def __init__(self, **kwargs):
        """ Pass a dictionary of arguments and they will be updated from the
        supplied data. """
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
        if changed:
            self.fire_event(pol.name)
        return changed

    def fire_event(self, name):
        """ Apply the appropriate policies on the resources that are observing
        this resource for the firing of a policy. """
        for immediately, resource, policy in  self.observers[name]:
            if immediately is False:
                raise NotImplementedError

            if resource.policy_override is not None and resource.policy_override != policy:
                raise error.ExecutionError("attempting to trigger policy '%s' on %r, but '%s' is already set" % (
                    policy, resource, resource.policy_override))
            resource.policy_override = policy

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
        if self.policy is not None:
            if self.policy.standard is not None:
                return self.policies[self.policy.standard.policy_name](self)
            else:
                if self.policy_override is not None:
                    return self.policies[self.policy_override](self)
                else:
                    return policy.NullPolicy(self)
        else:
            if self.policy_override is not None:
                return self.policies[self.policy_override](self)
            for p in self.policies.values():
                if p.default is True:
                    return p(self)
            else:
                return policy.NullPolicy(self)

    def dict_args(self):

        """ Return all argument names and values in a dictionary. If an
        argument has no default and has not been set, it's value in the
        dictionary will be None. """

        d = {}
        for a in self.__args__:
            d[a] = getattr(self, a, None)
        return d

    def __repr__(self):
        classname = getattr(self, '__resource_name__', self.__class__.__name__)
        return "%s[%s]" % (classname, self.name.encode("utf-8"))

    def __unicode__(self):
        classname = getattr(self, '__resource_name__', self.__class__.__name__)
        return u"%s[%s]" % (classname, self.name)


class ResourceBundle(ordereddict.OrderedDict):

    """ An ordered, indexed collection of resources. Pass in a specification
    that consists of scalars, lists and dictionaries and this class will
    instantiate the appropriate resources into the structure. """

    def __init__(self, specification=()):
        super(ResourceBundle, self).__init__()
        for resource in specification:
            if len(resource.keys()) > 1:
                raise error.ParseError("Too many keys in list item")
            typename, instances = resource.items()[0]
            if not isinstance(instances, list):
                instances = [instances]
            for instance in instances:
                self._create(typename, instance)


    def key_remap(self, kw):
        """ Maps - to _ to make resource attribute name more pleasant. """
        for k, v in kw.items():
            k = k.replace("-", "_")
            yield str(k),v

    def _create(self, typename, instance):
        if not isinstance(instance, dict):
            raise error.ParseError("Expected mapping for %s, got %s" % (typename, instance))
        kls = ResourceType.resources[typename](**dict(self.key_remap(instance)))
        self[kls.name] = kls

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

