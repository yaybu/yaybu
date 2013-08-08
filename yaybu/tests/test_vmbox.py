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
from yaybu.compute.vmware import VMBoxCache, VMBoxCollection, RemoteVMBox

cachedata = [
    {'id': '001',
     'url': "http://yaybu.com/image/ubuntu/12.04.2-server-amd64",
     },
    {'id': '002',
     'url': "http://yaybu.com/image/ubuntu/10.04.2-server-amd64",
     },
    {'id': '003',
     'url': "http://yaybu.com/image/debian/squeeze-i386",
     },
]

class TestImageDownload(unittest2.TestCase):
    
    def test_hash_headers_header_present(self):
        with patch('yaybu.compute.vmware.urllib2') as ul2:
            ul2.urlopen().info().getheaders.return_value = ["foo"]
            r = RemoteVMBox("http://www.example.com")
            self.assertEqual(r._hash_headers(), "foo")
        
    def test_hash_headers_header_not_present(self):
        with patch('yaybu.compute.vmware.urllib2') as ul2:
            ul2.urlopen().info().getheaders.return_value = []
            r = RemoteVMBox("http://www.example.com")
            self.assertEqual(r._hash_headers(), None)
    
    def test_hash_detached(self):
        with patch('yaybu.compute.vmware.urllib2') as ul2:
            ul2.urlopen().read.return_value = "foo"
            r = RemoteVMBox("http://www.example.com")
            self.assertEqual(r._hash_detached(), "foo")
    
    def test_get_hash_from_header(self):
        with patch('yaybu.compute.vmware.urllib2') as ul2:
            ul2.urlopen().info().getheaders.return_value = ["foo"]
            r = RemoteVMBox("http://www.example.com")
            self.assertEqual(r.get_hash(), "foo")
            
    def test_get_hash_from_detached(self):
        with patch('yaybu.compute.vmware.urllib2') as ul2:
            ul2.urlopen().info().getheaders.return_value = []
            ul2.urlopen().read.return_value = "foo"
            r = RemoteVMBox("http://www.example.com")
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
        r = RemoteVMBox("file://" + src)
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
        r = RemoteVMBox("file://" + src)
        self.assertRaises(ValueError, r.download, dst, progress)
        shutil.rmtree(d)
        
class TestVMBoxCache(unittest2.TestCase):

    def setUp(self):
        self.cachedir = tempfile.mkdtemp()
        for c in cachedata:
            cd = os.path.join(self.cachedir, c['id'])
            os.mkdir(cd)
            mp = os.path.join(cd, "metadata")
            metadata = {
                'name': c['url'],
                'created': str(datetime.datetime.now()),
                'hash': None
            }
            json.dump(metadata, open(mp, "w"))
        self.cache = VMBoxCache(self.cachedir)

    def tearDown(self):
        """ delete the cache dir """
        shutil.rmtree(self.cachedir)

    def test_scan(self):
        self.assertEqual(self.cache.items, {
             "http://yaybu.com/image/ubuntu/12.04.2-server-amd64": "001",
             "http://yaybu.com/image/ubuntu/10.04.2-server-amd64": "002",
             "http://yaybu.com/image/debian/squeeze-i386": "003",
             })

    def test_stray_file(self):
        open(os.path.join(self.cachedir, "foo"), "w").write("bar")
        self.test_scan()

    def test_stray_dir(self):
        os.mkdir(os.path.join(self.cachedir, "foo"))
        self.test_scan()

    def test_insert(self):
        f = tempfile.NamedTemporaryFile(delete=False)
        f.write("foo"*10000)
        f.close()
        h = hashlib.md5()
        h.update("foo"*10000)
        open(f.name + ".md5", "w").write(h.hexdigest())
        context = Mock()
        self.cache.insert("file://" + f.name, context)
        dirs = os.listdir(self.cachedir)
        self.assertEqual(len(dirs), 4)
        dirs.remove("001")
        dirs.remove("002")
        dirs.remove("003")
        self.assertEqual(len(dirs), 1)
        d = dirs[0]
        metadata = json.load(open(os.path.join(self.cachedir, d, "metadata")))
        self.assertEqual(metadata['name'], "file://" + f.name)
        self.assertEqual(metadata['hash'], h.hexdigest())




