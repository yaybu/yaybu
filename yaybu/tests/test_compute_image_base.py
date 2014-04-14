
import mock
import unittest2

import urllib2

from yaybu.compute.image import base
from yaybu.compute.image import error


class MockCloudImage(base.CloudImage):

    def hash_function(self):
        return str

    def remote_image_url(self):
        return "remote_image_url"

    def remote_hashfile_url(self):
        return "remote_hashfile_url"

    def image_hash(self, hashes):
        return hashes


class TestCloudImage(unittest2.TestCase):

    def setUp(self):
        self.cloud_image = MockCloudImage("pathname", "release", "arch")

    @mock.patch('urllib2.urlopen')
    @mock.patch('__builtin__.open')
    def test_fetch(self, m_open, m_urlopen):
        m_urlopen().read.side_effect = ["foo", "bar", ""]
        self.cloud_image.fetch()
        self.assertEqual(m_urlopen.call_args, mock.call('remote_image_url'))
        self.assertEqual(m_open.call_args, mock.call('pathname', 'w'))
        self.assertEqual(m_open().write.call_args_list, [mock.call('foo'), mock.call('bar')])

    @mock.patch('urllib2.urlopen')
    @mock.patch('__builtin__.open')
    def test_fetch_httperror(self, m_open, m_urlopen):
        m_urlopen.side_effect = urllib2.HTTPError(*[None] * 5)
        self.assertRaises(error.FetchFailedException, self.cloud_image.fetch)

    def test_decode_hashes_happy(self):
        d = self.cloud_image.decode_hashes("""
        foo bar
        baz quux
        """)
        self.assertEqual(d, {'bar': 'foo', 'quux': 'baz'})

    def test_decode_hashes_otherstuff(self):
        d = self.cloud_image.decode_hashes("""
        ----- PGP CRAP -----
        foo bar
        baz quux
        ----- MORE PGP CRAP -----

        stuff
        #wow
        """)
        self.assertEqual(d, {'bar': 'foo', 'quux': 'baz'})

    def test_decode_hashes_duplicate(self):
        self.assertRaises(KeyError, self.cloud_image.decode_hashes, """
        foo bar
        baz bar
        """)

    @mock.patch('urllib2.urlopen')
    def test_get_remote_hashes(self, m_urlopen):
        m_urlopen().read.return_value = """
        foo bar
        baz quux
        """
        self.assertEqual(self.cloud_image.get_remote_hashes(), {
            "bar": "foo",
            "quux": "baz",
        })

    @mock.patch('urllib2.urlopen')
    def test_get_remote_hashes_empty(self, m_urlopen):
        m_urlopen().read.return_value = ""
        self.assertEqual(self.cloud_image.get_remote_hashes(), {})

    @mock.patch('urllib2.urlopen')
    def test_get_remote_hashes_missing(self, m_urlopen):
        m_urlopen.side_effect = urllib2.HTTPError(*[None] * 5)
        self.assertEqual(self.cloud_image.get_remote_hashes(), {})
