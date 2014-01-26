# Copyright 2011-2014 Isotoma Limited
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


class ChangeRendererType(type):

    """ Keeps a registry of available renderers by type. The only types
    supported are text """

    renderers = {}

    def __new__(meta, class_name, bases, new_attrs):
        cls = type.__new__(meta, class_name, bases, new_attrs)
        if cls.renderer_for is not None:
            ChangeRendererType.renderers[
                (cls.renderer_type, cls.renderer_for)] = cls
        return cls


class ChangeRenderer(object):

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

    @classmethod
    def get(cls, change, logger):
        renderer_class = ChangeRendererType.renderers.get(
            (cls.renderer_type, change.__class__), cls)
        return renderer_class(logger, True)


class TextRenderer(ChangeRenderer):
    renderer_type = "text"


class Change(object):

    """ Base class for changes """

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def apply(self, ctx, renderer=None):
        """ Apply the specified change. The supplied renderer will be
        instantiated as below. """


class AttributeChange(Change):

    """ A change to one attribute of a file's metadata """
