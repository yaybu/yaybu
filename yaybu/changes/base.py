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


""" Classes that handle logging of changes. """

import abc


class Change(object):
    """ Base class for changes """

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def apply(self, ctx, renderer):
        """ Apply the specified change. The supplied renderer will be
        instantiated as below. """

class AttributeChange(Change):
    """ A change to one attribute of a file's metadata """

class ChangeRendererType(type):

    """ Keeps a registry of available renderers by type. The only types
    supported are text """

    renderers = {}

    def __new__(meta, class_name, bases, new_attrs):
        cls = type.__new__(meta, class_name, bases, new_attrs)
        if cls.renderer_for is not None:
            ChangeRendererType.renderers[(cls.renderer_type, cls.renderer_for)] = cls
        return cls

class ChangeRenderer:

    """ A class that knows how to render a change. """

    __metaclass__ = ChangeRendererType

    renderer_for = None
    renderer_type = None

    def __init__(self, logger, verbose):
        self.logger = logger
        self.verbose = verbose

    def render(self, logger):
        pass

    def info(self, message, *args):
        self.logger.info(message, *args)

    def notice(self, message, *args):
        self.logger.info(message, *args)

    def debug(self, message, *args):
        self.logger.info(message, *args)


class TextRenderer(ChangeRenderer):
    renderer_type = "text"


class _IckyNastyStub(object):

    # This is a temporary class whilst we refactor output to go through yaybu.core.ui

    def __init__(self, changelog, obj):
        self.changelog = changelog
        self.obj = obj

    def __enter__(self):
        obj = self.obj.__enter__()
        self.changelog.current_resource = obj
        return obj

    def __exit__(self, a, b, c):
        self.changelog.current_resource = None
        return self.obj.__exit__(a, b, c)


class ChangeLog:

    """ Orchestrate writing output to a changelog. """

    def __init__(self, context):
        self.changed = False
        self.current_resource = None
        self.ctx = context
        self.verbose = self.ctx.verbose
        self.ui = context.root.ui

    def resource(self, resource):
        return _IckyNastyStub(self, self.ctx.root.ui.section(str(resource)))

    def apply(self, change, ctx=None):
        """ Execute the change, passing it the appropriate renderer to use. """
        renderers = []
        text_class = ChangeRendererType.renderers.get(("text", change.__class__), TextRenderer)
        retval = change.apply(ctx or self.ctx, text_class(self, self.verbose))
        self.changed = self.changed or change.changed
        return retval

    def info(self, message, *args, **kwargs):
        if self.current_resource:
            self.current_resource.info(message, *args)
        else:
            self.ui.info(message, *args)

    def notice(self, message, *args, **kwargs):
        if self.current_resource:
            self.current_resource.notice(message, *args)
        else:
            self.ui.notice(message, *args)

    def debug(self, message, *args, **kwargs):
        if self.verbose:
            self.ui.debug(message, *args, **kwargs)

    def error(self, message, *args):
        self.ui.error(message, *args)
