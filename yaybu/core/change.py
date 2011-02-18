

class Change:
    pass

class AttributeChange(Change):
    """ A change to one attribute of a file's metadata """

class ChangeRenderer:
    def __init__(self, change, stream):
        self.change = change
        self.stream = stream

    def render(self, stream):
        pass


class HTMLRenderer(ChangeRenderer):
    pass

class TextRenderer(ChangeRenderer):
    pass

class ResourceChange:

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


class ChangeLog:

    def resource(self, resource):
        return ResourceChange()

    def record_change(self, change):
        pass

