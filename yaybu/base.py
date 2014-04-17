# Copyright 2013 Isotoma Limited
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

import logging

from yaybu import error
from yay import ast

logger = logging.getLogger(__name__)


class ActionContext(object):

    """
    I am some state that is shared between different Actions operation on the
    same AST Node (This must be a subclass of ast.PythonClass).

    Any data stored in ``outputs`` is coerced into the graph, and notification
    updates to other components may be generated.
    """

    def __init__(self, node):
        self.node = node
        self.outputs = {}
        self.changed = False


class ActionType(type):

    """
    I am a metaclass that maintains a registry of all available actions by part
    and name
    """

    actions = {}

    def __new__(meta, class_name, bases, attrs):
        if class_name != "Action" and "part" not in attrs:
            raise TypeError("An Action subclass must specify a 'part' attribute")

        cls = super(ActionType, meta).__new__(meta, class_name, bases, attrs)

        if "part" in attrs and "name" in attrs:
            part_registry = meta.actions.setdefault(attrs["part"], {})
            part_registry[attrs["name"]] = cls

        return cls


class Action(object):

    """
    I am an action taken against a part of your deployment architecture, for
    example turning it off or updating it.
    """

    __metaclass__ = ActionType

    dependencies = []

    def apply(self, context):
        pass

    def __repr__(self):
        if hasattr(self, "name"):
            return "Action(name='%s')" % self.name
        return "Action(class='%s')" % self.__class__.__name__


class Part(ast.PythonClass):

    """
    I am a component in a deployment architecture.

    I might have side effects: I might create and manage a LoadBalancer or
    deploy an Application.

    I might be an information source - such as a monitoring metric.

    I might be a event source, such as a notification about new Git tags.
    """

    ActionContext = ActionContext

    def apply(self):
        def resolve(action, resolved, unresolved):
            unresolved.add(action)
            for dep in action.dependencies:
                if dep in resolved:
                    continue
                if dep in unresolved:
                    raise error.TypeError('Action invalid due to circular reference between %r and %r' % (action, dep))
                resolve(dep, resolved, unresolved)
            unresolved.remove(action)
            resolved.append(action)
            return resolved

        actions = resolve(ActionType.actions[self.__class__][self.root.target], [], set())

        context = self.ActionContext(self)
        for action in actions:
            logger.debug("Applying %r" % action)
            action().apply(context)
        self.members.update(context.outputs)

        if context.changed:
            self.root.changed()

    def _resolve(self):
        # FIXME: There is a nicer way to do this without resolve, but more yay
        # refactoring required
        # This lets you find all Part's after doing a read-only resolve
        root = self.root
        if self not in root.actors:
            root.actors.append(self)
        return super(Part, self)._resolve()
