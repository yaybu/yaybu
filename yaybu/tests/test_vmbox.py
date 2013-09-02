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

import unittest2
import os
import tempfile
import hashlib
import json
import datetime
import shutil
import zipfile

from mock import MagicMock as Mock, call, patch

from yaybu.compute.vmware import VMBoxLibrary, RemoteVMBox, VMBoxImage


class TestVMBoxImage(unittest2.TestCase):

    def test_extract(self):
        with patch('yaybu.compute.vmware.ZipFile') as zf:
            zf().__enter__().namelist.return_value = ["foo", "bar", "baz"]
            vi = VMBoxImage("foo.zip")
            vi._store_metadata = Mock()
            vi._zcopy = Mock()
            ctx = Mock()
            vi.extract("/var/tmp/frob", ctx, {})
            vi._zcopy.assert_has_calls([
                call('/var/tmp/frob/foo', zf().__enter__(), 'foo'),
                call('/var/tmp/frob/bar', zf().__enter__(), 'bar'),
                call('/var/tmp/frob/baz', zf().__enter__(), 'baz'),
                ])
            vi._store_metadata.assert_has_calls([
                call('/var/tmp/frob', {})
                ])
            ctx.ui.throbber.assert_called_once_with("Extracting virtual machine")
            ctx.ui.throbber().__enter__().throb.assert_has_calls([
                call(),
                call(),
                call(),
                ])

    def test_extract_metadata(self):
        with patch('yaybu.compute.vmware.ZipFile') as zf:
            zf().__enter__().namelist.return_value = ["foo", "bar", "baz"]
            vi = VMBoxImage("foo.zip")
            vi._store_metadata = Mock()
            vi._zcopy = Mock()
            ctx = Mock()
            vi.extract("/var/tmp/frob", ctx, {"foo": "bar"})
            vi._store_metadata.assert_has_calls([
                call('/var/tmp/frob', {"foo": "bar"})
                ])

    def test_extract_metadata_vminfo(self):
        with patch('yaybu.compute.vmware.ZipFile') as zf:
            zf().__enter__().namelist.return_value = ["foo", "bar", "VM-INFO"]
            zf().__enter__().open().read.return_value = '{"baz": "quux"}'
            vi = VMBoxImage("foo.zip")
            vi._store_metadata = Mock()
            vi._zcopy = Mock()
            ctx = Mock()
            vi.extract("/var/tmp/frob", ctx, {"foo": "bar"})
            vi._store_metadata.assert_has_calls([
                call('/var/tmp/frob', {"foo": "bar", "baz": "quux"})
                ])

class TestRemoteVMBox(unittest2.TestCase):

    def _make_box(self, location):
        return RemoteVMBox(location, None, None)

    def test_hash_headers_header_present(self):
        with patch('yaybu.compute.vmware.urllib2') as ul2:
            ul2.urlopen().info().getheaders.return_value = ["foo"]
            r = self._make_box("http://www.example.com")
            self.assertEqual(r._hash_headers(), "foo")

    def test_hash_headers_header_not_present(self):
        with patch('yaybu.compute.vmware.urllib2') as ul2:
            ul2.urlopen().info().getheaders.return_value = []
            r = self._make_box("http://www.example.com")
            self.assertEqual(r._hash_headers(), None)

    def test_hash_detached(self):
        with patch('yaybu.compute.vmware.urllib2') as ul2:
            ul2.urlopen().read.return_value = "foo"
            r = self._make_box("http://www.example.com")
            self.assertEqual(r._hash_detached(), "foo")

    def test_get_hash_from_header(self):
        with patch('yaybu.compute.vmware.urllib2') as ul2:
            ul2.urlopen().info().getheaders.return_value = ["foo"]
            r = self._make_box("http://www.example.com")
            self.assertEqual(r.get_hash(), "foo")

    def test_get_hash_from_detached(self):
        with patch('yaybu.compute.vmware.urllib2') as ul2:
            ul2.urlopen().info().getheaders.return_value = []
            ul2.urlopen().read.return_value = "foo"
            r = self._make_box("http://www.example.com")
            self.assertEqual(r.get_hash(), "foo")

    def test_image_download_good_hash(self):
        h = hashlib.md5()
        progress = Mock()
        d = tempfile.mkdtemp()
        src = os.path.join(d, "src")
        dst = os.path.join(d, "dst")
        open(src, "w").write("foo"*10000)
        h.update("foo"*10000)
        open(src + ".md5", "w").write(h.hexdigest())
        r = self._make_box("file://" + src)
        r.download(dst, progress)
        self.assertEqual(open(dst).read(), "foo"*10000)
        progress.assert_has_calls([call(27), call(54), call(81), call(100)])
        shutil.rmtree(d)

    def test_image_download_wrong_hash(self):
        progress = Mock()
        d = tempfile.mkdtemp()
        src = os.path.join(d, "src")
        dst = os.path.join(d, "dst")
        open(src, "w").write("foo"*10000)
        open(src + ".md5", "w").write("foo")
        r = self._make_box("file://" + src)
        self.assertRaises(ValueError, r.download, dst, progress)
        shutil.rmtree(d)


    def test_context_manager(self):
        ## TODO
        pass

fixture = [
    { 'url': 'https://yaybu.com/library/ubuntu-12.04.2-amd64',
      'name': 'ubuntu-12.04.2-amd64',
      },
    { 'url': 'https://elsewhere.com/frob-14.7',
      'name': 'frob',
      },
]

class TestVMBoxLibrary(unittest2.TestCase):

    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.librarydir = os.path.join(self.root, "vmware", "library",)
        for f in fixture:
            d =  os.path.join(self.librarydir, f['name'])
            os.makedirs(d)
            mp = os.path.join(d, "VM-INFO")
            metadata = {
                'url': f['url'],
                'created': str(datetime.datetime.now()),
                'hash': None
            }
            json.dump(metadata, open(mp, "w"))
        self.library = VMBoxLibrary(self.root)

    def tearDown(self):
        """ delete the cache dir """
        shutil.rmtree(self.librarydir)

    def test_scan(self):
        self.assertEqual(self.library.library, {
            'https://yaybu.com/library/ubuntu-12.04.2-amd64': 'ubuntu-12.04.2-amd64',
            'https://elsewhere.com/frob-14.7': 'frob',
        })

    def test_stray_file(self):
        open(os.path.join(self.librarydir, "foo"), "w").write("bar")
        self.test_scan()

    def test_stray_dir(self):
        os.mkdir(os.path.join(self.librarydir, "foo"))
        self.test_scan()

    def test_get(self):
        f = tempfile.NamedTemporaryFile(delete=False)
        z = zipfile.ZipFile(f, "w", zipfile.ZIP_DEFLATED)
        z.writestr("foo", "foo"*1000)
        z.close()
        h = hashlib.md5()
        h.update(open(f.name).read())
        open(f.name + ".md5", "w").write(h.hexdigest())
        context = Mock()
        self.library.get("file://" + f.name, context, 'bar')
        dirs = os.listdir(self.librarydir)
        self.assertEqual(sorted(dirs), sorted([
            'ubuntu-12.04.2-amd64',
            'frob',
            'bar',
            ]))
        metadata = json.load(open(os.path.join(self.librarydir, 'bar', "VM-INFO")))
        self.assertEqual(metadata['url'], "file://" + f.name)
        self.assertEqual(metadata['hash'], h.hexdigest())
