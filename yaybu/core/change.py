
""" Classes that handle logging of changes. """

import abc
import sys
import logging
import types
import json

from yaybu.core import error

logger = logging.getLogger("audit")


class ResourceFormatter(logging.Formatter):

    """ Automatically add a header and footer to log messages about particular
    resources """

    def __init__(self, *args):
        logging.Formatter.__init__(self, *args)
        self.resource = None

    def format(self, record):
        next_resource = getattr(record, "resource", None)

        rv = u""

        # Is the logging now about a different resource?
        if self.resource != next_resource:

            # If there was already a resource, let us add a footer
            if self.resource:
                rv += self.render_resource_footer()

            self.resource = next_resource

            # Are we now logging for a new resource?
            if self.resource:
                rv += self.render_resource_header()

        formatted = logging.Formatter.format(self, record)

        if self.resource:
            rv += "\r\n".join("| %s" % line for line in formatted.splitlines()) + "\r"
        else:
            rv += formatted

        return rv

    def render_resource_header(self):
        header = unicode(self.resource)

        rl = len(header)
        if rl < 80:
            total_minuses = 77 - rl
            minuses = total_minuses/2
            leftover = total_minuses % 2
        else:
            minuses = 4
            leftover = 0

        return u"/%s %s %s\n" % ("-"*minuses,
                                 header,
                                 "-"*(minuses + leftover))

    def render_resource_footer(self):
        return u"\%s\n\n" % ("-" *79,)


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

        # We wrap the logger so it always has context information
        logger = logging.getLogger("yaybu.changelog")
        self.logger = logging.LoggerAdapter(logger, dict(resource=unicode(resource)))

    def info(self, message, *args):
        self.logger.info(message, *args)

    def notice(self, message, *args):
        self.logger.info(message, *args)

    def __enter__(self):
        self.changelog.current_resource = self
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.exc_type = exc_type
        self.exc_val = exc_val
        self.exc_tb = exc_tb

        if self.exc_val is not None:
            self.notice("Exception: %s" % (self.exc_val,))

        self.changelog.current_resource = None


class ChangeLog:

    """ Orchestrate writing output to a changelog. """

    def __init__(self, context):
        self.current_resource = None
        self.ctx = context
        self.verbose = self.ctx.verbose

        self.logger = logging.getLogger("yaybu.changelog")

        self.configure_session_logging()
        self.configure_audit_logging()

    def configure_session_logging(self):
        root = logging.getLogger("yaybu.changelog")
        root.setLevel(logging.INFO)

        if len(root.handlers):
            # Session logging has already been configured elsewhere?
            return

        handler = logging.StreamHandler(sys.stdout)
        #handler.setFormatter(logging.Formatter("%(message)s"))
        handler.setFormatter(ResourceFormatter("%(message)s"))
        root.addHandler(handler)

    def configure_audit_logging(self):
        """ configure the audit trail to log to file or to syslog """

        if self.ctx.simulate:
            return

        options = self.ctx.options.get("auditlog", {})
        mode = options.get("mode", "off")

        if mode == "off":
            return

        levels = {
            'debug': logging.DEBUG,
            'info': logging.INFO,
            'warning': logging.WARNING,
            'error': logging.ERROR,
            'critical': logging.CRITICAL,
            }

        level = levels.get(options.get("level", "info"), None)
        if level is None:
            raise KeyError("Log level %s not recognised, terminating" % option["level"])

        root = logging.getLogger()

        if mode == "file":
            handler = logging.FileHandler(options.get("logfile", "/var/log/yaybu.log"))
            #handler.setFormatter(logging.Formatter("%(message)s"))
            handler.setFormatter(ResourceFormatter("%(asctime)s %(message)s"))
            root.addHandler(handler)

        elif mode == "syslog":
            facility = getattr(logging.handlers.SysLogHandler, "LOG_LOCAL%s" % options.get("facility", "7"))
            handler = logging.handlers.SysLogHandler("/dev/log", facility=facility)
            formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
            handler.setFormatter(formatter)
            logging.getLogger().addHandler(handler)

    def write(self, line=""):
        #FIXME: Very much needs removing
        self.logger.info(line)

    def resource(self, resource):
        return ResourceChange(self, resource)

    def apply(self, change):
        """ Execute the change, passing it the appropriate renderer to use. """
        renderers = []
        text_class = ChangeRendererType.renderers.get(("text", change.__class__), None)
        return change.apply(text_class(self, self.verbose))

    def info(self, message, *args, **kwargs):
        """ Write a textual information message. This is used for both the
        audit trail and the text console log. """
        if self.current_resource:
            self.current_resource.info(message, *args)
        else:
            self.logger.info(message, *args)

    def notice(self, message, *args, **kwargs):
        """ Write a textual notification message. This is used for both the
        audit trail and the text console log. """
        if self.current_resource:
            self.current_resource.notice(message, *args)
        else:
            self.logger.info(message, *args)

    def debug(self, message, *args, **kwargs):
        pass

    def error(self, message, *args):
        self.logger.error(message, *args)

    def handle(self, record):
        self.logger.handle(record)


class RemoteHandler(logging.Handler):

    def __init__(self, connection):
        logging.Handler.__init__(self)
        self.connection = connection

    def emit(self, record):
        data = json.dumps(record.__dict__)

        self.connection.request("POST", "/changelog/", data, {"Content-Length": len(data)})
        rsp = self.connection.getresponse()

        lngth = rsp.getheader("Content-Length", 0)
        rsp.read(lngth)


class RemoteChangeLog(ChangeLog):

    def configure_session_logging(self):
        root = logging.getLogger()
        root.setLevel(logging.INFO)

        handler = RemoteHandler(self.ctx.connection)
        handler.setFormatter(logging.Formatter("%(message)s"))
        root.addHandler(handler)

    def configure_audit_logging(self):
        # We don't want to try and log changes in syslog on the box we are pressing go on,
        # only the box we are deploying to. So no audit logging here.
        pass

