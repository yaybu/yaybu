import unittest2
import os
import tempfile
import mock
import json
import datetime
import shutil
from mock import MagicMock as Mock, call

from yaybu.compute.vmware import VMBoxCache, VMBoxCollection, image_download

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

    def test_image_download(self):
        progress = Mock()
        d = tempfile.mkdtemp()
        src = os.path.join(d, "src")
        dst = os.path.join(d, "dst")
        open(src, "w").write("foo"*10000)
        image_download("file://" + src, dst, progress)
        self.assertEqual(open(dst).read(), "foo"*10000)
        progress.assert_has_calls([call(27), call(54), call(81), call(100)])
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
                'created': str(datetime.datetime.now())
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




