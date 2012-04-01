# Copyright 2011 Isotoma Limited
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


import unittest, mock
from yaybu.core import error
from yaybu.providers.filesystem import files

class TestFileProvider(unittest.TestCase):

    def test_simple(self):
        f = mock.Mock()
        f.name = "/tmp/hello"
        f.template = None

        ctx = mock.Mock()
        ctx.vfs.exists.return_value = False

        p = files.File(f)
        changed = p.apply(ctx)

        self.failUnlessEqual(changed, True)


class TestFileDelete(unittest.TestCase):

    def test_file_exists(self):
        f = mock.Mock()
        f.name = "/tmp/test_file_exists"

        ctx = mock.Mock()
        ctx.vfs.exists.return_value = True
        ctx.vfs.isfile.return_value = True

        p = files.RemoveFile(f)
        changed = p.apply(ctx)

        self.failUnlessEqual(changed, True)
        ctx.vfs.delete.assert_called_once_with("/tmp/test_file_exists")

    def test_file_doesnt_exist(self):
        f = mock.Mock()
        f.name = "/tmp/test_file_exists"

        ctx = mock.Mock()
        ctx.vfs.exists.return_value = False
        ctx.vfs.isfile.return_value = True

        p = files.RemoveFile(f)
        changed = p.apply(ctx)

        self.failUnlessEqual(changed, False)
        self.failUnlessEqual(ctx.vfs.delete.called, False)

    def test_exists_notfile(self):
        f = mock.Mock()
        f.name = "/tmp/test_file_exists"

        ctx = mock.Mock()
        ctx.vfs.exists.return_value = True
        ctx.vfs.isfile.return_value = False

        p = files.RemoveFile(f)

        self.failUnlessRaises(error.InvalidProvider, p.apply, ctx)
        self.failUnlessEqual(ctx.vfs.delete.called, False)

