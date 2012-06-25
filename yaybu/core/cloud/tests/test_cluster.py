
import unittest
from StringIO import StringIO
import yaml
from yaybu.core.cloud import cluster

class TestStateMarshaller(unittest.TestCase):
    
    def test_load(self):
        data = {}
        data['version'] = 1
        data['nodes'] = [
            {'role': 'mailserver',
             'index': 0,
             'name': 'foo',
             'their_name': 'fooX',
             },
            {'role': 'mailserver',
             'index': 1,
             'name': 'bar',
             'their_name': 'barX',
             },
            {'role': 'appserver',
             'index': 0,
             'name': 'baz',
             'their_name': 'bazX',
             }]
        stream = StringIO(yaml.dump(data))
        output = {}
        output['mailserver'] = [
            cluster.Node(0, 'foo', 'fooX'),
            cluster.Node(1, 'bar', 'barX'),
            ]
        output['appserver'] = [
            cluster.Node(0, 'baz', 'bazX')
            ]
        self.assertEqual(dict(cluster.StateMarshaller.load(stream)), output)

    def test_save(self):
        roles = {}
        roles['mailserver'] = cluster.Role('mailserver', None, None, None, None)
        roles['appserver'] = cluster.Role('appserver', None, None, None, None)
        roles['mailserver'].nodes[0] = cluster.Node(0, 'foo', 'fooX')
        roles['mailserver'].nodes[1] = cluster.Node(1, 'bar', 'barX')
        roles['appserver'].nodes[0] = cluster.Node(0, 'baz', 'bazX')
        result = yaml.load(cluster.StateMarshaller.as_stream(roles))
        self.assertEqual(result['version'], 1)
        self.assertEqual(sorted(result['nodes']),
                         sorted([
                             {'role': 'mailserver', 
                              'index': 0, 
                              'name': 'foo', 
                              'their_name': 'fooX'},
                             {'role': 'mailserver',
                              'index': 1,
                              'name': 'bar',
                              'their_name': 'barX'},
                             {'role': 'appserver',
                              'index': 0,
                              'name': 'baz',
                              'their_name': 'bazX'},
                             ])
                         )
        