
""" Classes that handle logging of changes. """

import abc
import sys
import logging

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
    supported are text and html and a class may not implement both. """

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

class HTMLRenderer(ChangeRenderer):
    renderer_type = "html"

class TextRenderer(ChangeRenderer):
    renderer_type = "text"

class ResourceChange(object):

    """ A context manager that handles logging per resource. This allows us to
    elide unchanged resources, which is the default logging output option. """

    def __init__(self, changelog, resource):
        self.changelog = changelog
        self.resource = resource
        self.html_messages = []
        self.rendered = False

    def __enter__(self):
        self.changelog.current_resource = self

    def render_resource_header(self):
        if self.rendered:
            return
        self.rendered = True
        rl = len(str(self.resource))
        if rl < 80:
            minuses = (77 - rl)/2
        else:
            minuses = 4
        self.changelog.write("/%s %r %s" % ("-"*minuses,
                                            self.resource,
                                            "-"*minuses))

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

    def html_info(self, message):
        self.html_messages.append((0, message))

    def html_notice(self, message):
        self.html_messages.append((1, message))

    def simulation_info(self, message):
        simlog.info(message)

    def simulation_notice(self, message):
        simlog.notice(message)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.exc_type = exc_type
        self.exc_val = exc_val
        self.exc_tb = exc_tb
        self.changelog.current_resource = None
        if self.rendered:
            self.render_resource_footer()
        if self.html_messages:
            self.changelog.write("<h2>%s</h2>" % self.resource)
            self.changelog.write("<ol>")
            for level, msg in self.messages:
                if level == 0:
                    self.changelog.write("<li>%s</li>" % msg)
                elif level == 1:
                    self.changelog.write("<li><b>%s</b></li>" % msg)
            self.changelog.write("</ol>")

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
        if self.ctx.html is not None:
            self.ctx.html.write(line)
            sys.stdout.write("\n")
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
        if self.ctx.html is not None:
            html_class = ChangeRendererType.renderers.get(("html", change.__class__), None)
            if html_class:
                renderers.append(html_class(self, self.verbose))
        multi = MultiRenderer(*renderers)
        return change.apply(multi)

    def info(self, message, *args, **kwargs):
        """ Write a textual information message. This is used for both the
        audit trail and the text console log. """
        formatted = message.format(*args, **kwargs)
        logger.info(formatted)
        if self.ctx.html is None:
            self.current_resource.info(formatted)

    def notice(self, message, *args, **kwargs):
        """ Write a textual notification message. This is used for both the
        audit trail and the text console log. """
        formatted = message.format(*args, **kwargs)
        logger.warning(formatted)
        if self.ctx.html is None:
            self.current_resource.notice(formatted)

    def html_info(self, message, *args, **kwargs):
        """ Write an html information message. """
        formatted = message.format(*args, **kwargs)
        if self.ctx.html is not None:
            self.current_resource.html_info(formatted)

    def html_notice(self, message, *args, **kwargs):
        """ Write an html notification message. """
        formatted = message.format(*args, **kwargs)
        if self.ctx.html is not None:
            self.current_resource.html_notice(formatted)
