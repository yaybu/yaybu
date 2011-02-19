
class Change:
    pass

class AttributeChange(Change):
    """ A change to one attribute of a file's metadata """

class MetaChangeRenderer(type):

    renderers = {}

    def __new__(meta, class_name, bases, new_attrs):
        cls = type.__new__(meta, class_name, bases, new_attrs)
        if cls.renderer_for is not None:
            MetaChangeRenderer.renderers[(cls.renderer_type, cls.renderer_for)] = cls
        return cls

class ChangeRenderer:

    __metaclass__ = MetaChangeRenderer

    renderer_for = None
    renderer_type = None

    def __init__(self, original):
        self.original = original

    def render(self, logger):
        pass

class HTMLRenderer(ChangeRenderer):
    renderer_type = "html"

class TextRenderer(ChangeRenderer):
    renderer_type = "text"

class ResourceChange(Change):

    def __init__(self, changelog, resource):
        self.changelog = changelog
        self.resource = resource
        self.state = "enter"

    def __enter__(self):
        self.changelog.change(self)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.state = "exit"
        self.exc_type = exc_type
        self.exc_val = exc_val
        self.exc_tb = exc_tb
        self.changelog.change(self)

class ResourceChangeTextRenderer(TextRenderer):

    renderer_for = ResourceChange

    def render(self, logger):
        if self.original.state == "enter":
            logger.log("change", "start", resource=self.original.resource)
        else:
            logger.log("change", "end", resource=self.original.resource)

class ChangeLog:

    """ Orchestrate writing output to a changelog. """

    def __init__(self, shell, change, html):
        self.shell = shell
        self.change = change
        self.html = html

    def resource(self, resource):
        return ResourceChange(self, resource)

    def log_multiline(self, facility, message):
        for l in message.splitlines():
            print >>self.stream, "    %s" % l

    def log(self, facility, message, *args, **kwargs):
        resource = kwargs.pop("resource", None)
        print >>self.stream, repr(resource), facility, message.format(*args, **kwargs)

    def change(self, change):
        renderer = MetaChangeRenderer.renderers[(self.log_type, change.__class__)]
        renderer(change).render(self)


