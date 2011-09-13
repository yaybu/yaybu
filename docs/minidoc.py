from sphinx.ext.autodoc import Documenter

import sys

def format_name(self):
    if self.objpath:
        return self.objpath[-1]

def add_directive_header(self, sig):
    """Add the directive header and options to the generated content."""
    domain = getattr(self, 'domain', 'py')
    directive = getattr(self, 'directivetype', self.objtype)
    name = self.format_name()
    self.add_line(u'.. %s:%s:: %s%s' % (domain, directive, name, sig),
                '<autodoc>')
    if self.options.noindex:
        self.add_line(u'   :noindex:', '<autodoc>')

Documenter.format_name = format_name
Documenter.add_directive_header = add_directive_header


