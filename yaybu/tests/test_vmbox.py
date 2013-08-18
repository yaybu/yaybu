import unittest2
import os
import tempfile
import hashlib
import mock
import json
import datetime
import shutil
from mock import MagicMock as Mock, call, patch

from yaybu.compute import vmware
from yaybu.compute.vmware import VMBoxLibrary, RemoteVMBox

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
      'name': 'foo',
      },
]

class TestVMBoxLibrary(unittest2.TestCase):

    def setUp(self):
        self.root = tempfile.mkdtemp()
        for f in fixture:
            d = os.path.join(self.root, "vmware", "library", f['name'])
            os.makedirs(d)
            mp = os.path.join(d, "metadata")
            metadata = {
                'url': f['url'],
                'created': str(datetime.datetime.now()),
                'hash': None
            }
            json.dump(metadata, open(mp, "w"))
        self.library = VMBoxLibrary(self.root)

    def test_scan(self):
        self.assertEqual(self.library.library, {
            'https://yaybu.com/library/ubuntu-12.04.2-amd64': 'ubuntu-12.04.2-amd64',
            'https://elsewhere.com/frob-14.7': 'foo',
        })


    #def tearDown(self):
        #""" delete the cache dir """
        #shutil.rmtree(self.librarydir)

    #def test_scan(self):
        #self.assertEqual(self.cache.items, {
             #"http://yaybu.com/image/ubuntu/12.04.2-server-amd64": "001",
             #"http://yaybu.com/image/ubuntu/10.04.2-server-amd64": "002",
             #"http://yaybu.com/image/debian/squeeze-i386": "003",
             #})

    #def test_stray_file(self):
        #open(os.path.join(self.librarydir, "foo"), "w").write("bar")
        #self.test_scan()

    #def test_stray_dir(self):
        #os.mkdir(os.path.join(self.librarydir, "foo"))
        #self.test_scan()

    #def test_insert(self):
        #f = tempfile.NamedTemporaryFile(delete=False)
        #f.write("foo"*10000)
        #f.close()
        #h = hashlib.md5()
        #h.update("foo"*10000)
        #open(f.name + ".md5", "w").write(h.hexdigest())
        #context = Mock()
        #self.cache.insert("file://" + f.name, context)
        #dirs = os.listdir(self.librarydir)
        #self.assertEqual(len(dirs), 4)
        #dirs.remove("001")
        #dirs.remove("002")
        #dirs.remove("003")
        #self.assertEqual(len(dirs), 1)
        #d = dirs[0]
        #metadata = json.load(open(os.path.join(self.librarydir, d, "metadata")))
        #self.assertEqual(metadata['name'], "file://" + f.name)
        #self.assertEqual(metadata['hash'], h.hexdigest())




