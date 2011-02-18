
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

    def render(self, stream):
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

    def render(self, stream):
        if self.original.state == "enter":
            print >>stream, "Start Processing %r" % self.original.resource
        else:
            print >>stream, "End Processing %r" % self.original.resource

class ChangeLog:

    """ Orchestrate writing output to a changelog. """

    def __init__(self, log_type, stream):
        self.log_type = log_type
        self.stream = stream

    def resource(self, resource):
        return ResourceChange(self, resource)

    def change(self, change):
        renderer = MetaChangeRenderer.renderers[(self.log_type, change.__class__)]
        renderer(change).render(self.stream)


