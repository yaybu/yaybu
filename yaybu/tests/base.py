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

from optparse import OptionParser
import os
import tempfile

try:
    import unittest2 as unittest
except ImportError:
    import unittest

from yaybu.core.config import Config
from yaybu.core.command import YaybuCmd
from yaybu import error


class ChangeStillOutstanding(Exception):
    pass


class TestCase(unittest.TestCase):

    Config = Config

    def _config(self, contents):
        f = tempfile.NamedTemporaryFile(delete=False)
        f.write(contents)
        f.close()
        path = os.path.realpath(f.name)
        self.addCleanup(os.unlink, path)
        return path

    def _get_graph(self, config, *args):
        config_file = self._config(config)
        config_dir = os.path.dirname(config_file)
        p = OptionParser()
        y = YaybuCmd(config_file, ypath=(config_dir, ))
        y.Config = self.Config
        y.verbose = 2
        y.debug = True
        y.opts_up(p)
        return y._get_graph(*p.parse_args(list(args)))

    def _do(self, action, config, *args):
        config_file = self._config(config)
        config_dir = os.path.dirname(config_file)
        p = OptionParser()
        y = YaybuCmd(config_file, ypath=(config_dir, ))
        y.Config = self.Config
        y.verbose = 2
        y.debug = True
        getattr(y, "opts_" + action)(p)
        return getattr(y, "do_" + action)(*p.parse_args(list(args)))

    def _up(self, config, *args):
        return self._do("up", config, *args)

    def up(self, config, *args):
        # Every call to self.up validates that simulate and actual mode works
        # It also enforces:
        #  * Parts are idempotent
        #  * Simulate mode is read only
        #  * Simulate mode detects the same failures as a deployment

        self._up(config, "-s", *args)

        try:
            self._up(config, *args)
        except error.NothingChanged:
            raise RuntimeError(
                "Either simulate wasn't read-only or simulate didn't detect change was required")

        try:
            self._up(config, *args)
        except error.NothingChanged:
            return
        raise ChangeStillOutstanding("Action wasn't idempotent")

    def destroy(self, config, *args):
        return self._do("destroy", config, *args)

    if not hasattr(unittest.TestCase, "addCleanup"):
        def __init__(self, *args, **kwargs):
            self.cleanups = []
            super(TestCase, self).__init__(*args, **kwargs)

        def addCleanup(self, func, *args, **kwargs):
            self.cleanups.append((func, args, kwargs))

        def tearDown(self):
            for func, args, kwargs in reversed(self.cleanups):
                try:
                    func(*args, **kwargs)
                except:
                    pass

        def assertIn(self, a, b):
            assert a in b, "%r not in %r" % (a, b)
