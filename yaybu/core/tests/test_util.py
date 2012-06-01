import wingdbstub

import unittest
from yay import stringbuilder
from yaybu.core.util import EncryptedConfigAdapter

def secret(value):
    s = stringbuilder.String()
    s.add_secret(value)
    return s

plain_config = {
    'string': 'foo',
    'list': ['foo', 'bar', 'baz'],
    'dict': {
        'string': 'foo',
        'list': ['foo', 'bar', 'baz'],
    },
}

encrypted_config = {
    'string': secret('foo'),
    'list': ['foo', secret('bar'), 'baz'],
    'dict': {
        'string': secret('foo'),
        'list': ['foo', secret('bar'), 'baz'],
    },
}

class TestEncryptedConfigAdapter(unittest.TestCase):
    
    def _tests(self, e):
        self.assertEqual(e['string'], 'foo')
        self.assertEqual(list(e['list']), ['foo', 'bar', 'baz'])
        self.assertEqual(e['dict']['string'], 'foo')
        self.assertEqual(list(e['dict']['list']), ['foo', 'bar', 'baz'])
        
    def test_plain(self):
        e = EncryptedConfigAdapter(plain_config)
        self._tests(e)
        
    def test_encrypted(self):        
        e = EncryptedConfigAdapter(encrypted_config)
        self._tests(e)
    
    
