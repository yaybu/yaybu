
""" Classes that handle logging of changes. """

import abc
import sys
import logging
import types

from yaybu.core import error

logger = logging.getLogger("audit")
simlog = logging.getLogger("simulation")

class Change(object):
    """ Base class for changes """

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def apply(self, renderer):
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

    def simulation_info(self, message):
        self.logger.simlog_info(message)

    def simulation_notice(self, message):
        self.logger.simlog_notice(message)

    def render(self, logger):
        pass

class TextRenderer(ChangeRenderer):
    renderer_type = "text"

class ResourceChange(object):

    """ A context manager that handles logging per resource. This allows us to
    elide unchanged resources, which is the default logging output option. """

    def __init__(self, changelog, resource):
        self.changelog = changelog
        self.resource = resource
        self.rendered = False

    def __enter__(self):
        self.changelog.current_resource = self

    def render_resource_header(self):
        if self.rendered:
            return
        self.rendered = True
        rl = len(unicode(self.resource))
        if rl < 80:
            total_minuses = 77 - rl
            minuses = total_minuses/2
            leftover = total_minuses % 2
        else:
            minuses = 4
        self.changelog.write("/%s %r %s" % ("-"*minuses,
                                            self.resource,
                                            "-"*(minuses + leftover)))

    def render_resource_footer(self):
        self.changelog.write("\%s" % ("-" *79,))
        self.changelog.write()

    def info(self, message):
        if self.changelog.verbose >= 2:
            self.render_resource_header()
            self.changelog.write("|====> %s" % message)

    def notice(self, message):
        if self.changelog.verbose >= 1:
            self.render_resource_header()
            self.changelog.write("| %s" % message)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.exc_type = exc_type
        self.exc_val = exc_val
        self.exc_tb = exc_tb
        if self.exc_val is not None:
            self.notice("Exception: %s" % (self.exc_val,))
        self.changelog.current_resource = None
        if self.rendered:
            self.render_resource_footer()

class RendererMethodProxy:

    def __init__(self, multi, name):
        self.multi = multi
        self.name = name

    def __call__(self, *args, **kwargs):
        self.multi.delegate(self.name, args, kwargs)

class MultiRenderer:

    def __init__(self, *renderers):
        self.renderers = renderers

    def __getattr__(self, name):
        return RendererMethodProxy(self, name)

    def delegate(self, name, args, kwargs):
        for renderer in self.renderers:
            getattr(renderer, name)(*args, **kwargs)

class ChangeLog:

    """ Orchestrate writing output to a changelog. """

    def __init__(self, context):
        self.current_resource = None
        self.ctx = context
        self.verbose = self.ctx.verbose

    def write(self, line=""):
        if type(line) is types.UnicodeType:
            sys.stdout.write(line.encode("utf-8"))
        else:
            sys.stdout.write(line)
        sys.stdout.write("\n")

    def resource(self, resource):
        return ResourceChange(self, resource)

    def apply(self, change):
        """ Execute the change, passing it the appropriate renderer to use. """
        renderers = []
        text_class = ChangeRendererType.renderers.get(("text", change.__class__), None)
        if text_class:
            renderers.append(text_class(self, self.verbose))
        multi = MultiRenderer(*renderers)
        return change.apply(multi)

    def simlog_notice(self, msg):
        simlog.notice(msg)

    def simlog_info(self, msg):
        simlog.info(msg)

    def info(self, message, *args, **kwargs):
        """ Write a textual information message. This is used for both the
        audit trail and the text console log. """
        formatted = message.format(*args, **kwargs)
        self.current_resource.info(formatted)

    def notice(self, message, *args, **kwargs):
        """ Write a textual notification message. This is used for both the
        audit trail and the text console log. """
        formatted = message.format(*args, **kwargs)
        self.current_resource.notice(formatted)


class RemoteChangeLog(ChangeLog):

    def do(self, method, msg):
        self.ctx.connection.request("POST", "/changelog/" + method, msg, {"Content-Length": len(msg)})
        rsp = self.ctx.connection.getresponse()

    def write(self, line=""):
        self.do("write", line)

    def simlog_notice(self, msg):
        self.do("simlog_notice", msg)

    def simlog_info(self, msg):
        self.do("simlog_info", msg)

