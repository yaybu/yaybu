import unittest2
import os
import tempfile
import mock
import yaml
import datetime
import shutil
from mock import MagicMock as Mock

from yaybu.compute.vmware import VMBoxCache, VMBoxCollection

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

class TestVMBoxCache(unittest2.TestCase):

    def setUp(self):
        self.cachedir = tempfile.mkdtemp()
        for c in cachedata:
            cd = os.path.join(self.cachedir, c['id'])
            os.mkdir(cd)
            mp = os.path.join(cd, "metadata.yaml")
            metadata = {
                'name': c['url'],
                'created': str(datetime.datetime.now())
            }
            yaml.safe_dump(metadata, open(mp, "w"), default_flow_style=False)
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






