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

from unittest2 import TestCase
import mock

from yaybu import error
from yaybu.util import render_string


class TestTemplate(TestCase):

    def setUp(self):
        self.context = mock.Mock()
        self.paths = {}
        def _get_file(path):
            if path in self.paths:
                return self.paths[path]
            raise error.MissingAsset(path)
        self.context.get_file.side_effect = _get_file

    def add_path(self, path, contents, labels=None):
        fp = mock.Mock()
        fp.read.side_effect = lambda: contents
        fp.labels = labels or []
        self.paths[path] = fp

    def test_simple_variable(self):
        args = {"hello": "world"}
        self.assertEqual(render_string(self.context, "{{ hello }}", args)[0].strip(), "world")

    def test_for_loop(self):
        contents = """
        {% for f in foo %}{{ f }},{% endfor %}
        """
        args = {"foo": [1,2,3]}
        self.assertEqual(render_string(self.context, contents, args)[0].strip(), "1,2,3,")

    def _assert_parse_error(self, contents, args=None):
        self.assertRaises(error.ParseError, render_string, self.context, contents, args or {})

    def test_grammar_error(self):
        contents = """
        {% for foo in simple_variable %}
        {{ foo }}
        {% end for %}
        """
        self._assert_parse_error(contents)

    def _assert_key_error(self, contents, args=None):
        self.assertRaises(error.NoMatching, render_string, self.context, contents, args or {})

    def test_strict_error_simple_variable(self):
        contents = """
        {{ simple_variable }}
        """
        self._assert_key_error(contents)

    def test_strict_error_for_loop(self):
        contents = """
        {% for foo in simple_variable %}
        {{ hello }}
        {% endfor %}
        """
        self._assert_key_error(contents)

    def test_allow_test_on_undefined(self):
        contents = """
        {% if foo %}
        hello
        {% endif %}
        """
        self.assertEqual(render_string(self.context, contents, {})[0].strip(), "")

    def test_allow_test_on_undefined_2(self):
        contents = """
        {% if not foo %}
        hello
        {% endif %}
        """
        self.assertEqual(render_string(self.context, contents, {})[0].strip(), "hello")

    def test_includes_work(self):
        self.add_path("test1", "hello world")
        contents = """
        {% include "test1" %}
        """
        self.assertEqual(render_string(self.context, contents, {})[0].strip(), "hello world")

    def test_includes_can_access_vars(self):
        self.add_path("test1", "hello {{ name }}")
        contents = """
        {% include "test1" %}
        """
        args = {"name": "world"}
        self.assertEqual(render_string(self.context, contents, args)[0].strip(), "hello world")

    def test_includes_not_secret_by_default(self):
        self.add_path("test1", "hello: world\n")
        contents = """
        {% include "test1" %}
        """
        self.assertEqual(render_string(self.context, contents, {})[1], False)

    def test_includes_tainted_by_secrets(self):
        self.add_path("test1", "hello: world\n", ['secret'])
        contents = """
        {% include "test1" %}
        """
        self.assertEqual(render_string(self.context, contents, {})[1], True)

    def test_missing_asset_exception_on_include(self):
        contents = """
        {% include "test1" %}
        """
        self.assertRaises(error.MissingAsset, render_string, self.context, contents, {})

    def test_template_error(self):
        contents = """
        {{ 0 / 0 }}
        """
        self.assertRaises(error.TemplateError, render_string, self.context, contents, {})

