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


from jinja2 import Environment, BaseLoader, TemplateNotFound, StrictUndefined
from jinja2.exceptions import UndefinedError, TemplateSyntaxError

from yaybu import error


class LessStrictUndefined(StrictUndefined):
    """
    Fail strictly if someone uses a variable that isn't defined in the context
    expression - but still allow boolean checks
    """
    def __nonzero__(self):
        return False


class TemplateLoader(BaseLoader):
    """
    A template loader that searches for templates using the Yaybu openers sytem.
    This means that templates can be fetched over http and can even be
    encrypted with GPG.

    It tracks whether it has been used to open any encrypted templates and sets
    a taint flag if it has.
    """
    def __init__(self, ctx):
        self.ctx = ctx
        self.secret = False

    def get_source(self, environment, template):
        f = self.ctx.get_file(template)
        source = f.read()
        self.secret = self.secret or "secret" in f.labels
        return source, template, lambda: False


def get_template_environment(context):
    """
    Sets up a standard Yaybu template rendering environment

    In particular Yaybu has these requirements:

      * The use of line_statement_prefix - to enable strong control over whitespace
      * The use of a custom template loader that respects the yaybu search path
      * The use of stricter undefined error handling than provided by Jinja by default

    """
    loader = TemplateLoader(context)
    env = Environment(
        loader=loader,
        line_statement_prefix='%',
        undefined=LessStrictUndefined,
        )
    return env


def _call(callable, *args, **kwargs):
    try:
        return callable(*args, **kwargs)
    except TemplateSyntaxError as e:
        raise error.ParseError(str(e))
    except UndefinedError as e:
        raise error.NoMatching(str(e))


def render_string(context, contents, arguments):
    """
    Set up a template environment that searches for referenced templates on the
    Yaybu search path and use it to render a string.

    Returns the rendered template and a boolean that is True if a template used
    directly or indirectly was encrypted.

    Template exceptions will be mapped to Yaybu expections.
    """
    env = get_template_environment(context)
    template = _call(env.from_string, contents)
    rendered = _call(template.render, arguments) + "\n"
    return rendered, env.loader.secret


def render_template(context, template, arguments):
    """
    Set up a template environment that searches for templates on the Yaybu
    search path and use it to render the specified template.

    Returns the rendered template and a boolean that is True if a template used
    directly or indirectly was encrypted.

    Template exceptions will be mapped to Yaybu exceptions.
    """
    env = get_template_environment(context)
    template = _call(env.get_template, template)
    rendered = _call(template.render, arguments) + "\n"
    return rendered, env.loader.secret

