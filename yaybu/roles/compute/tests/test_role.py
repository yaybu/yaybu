import os
import unittest
from mock import MagicMock as Mock
from StringIO import StringIO
import tempfile
import yaml
from yaybu.core.cloud import cluster
from libcloud.storage.types import ContainerDoesNotExistError, ObjectDoesNotExistError
from yaybu.core.cloud import role

from yaybu.roles.compute.role import Compute

roles1 = """

clouds:
    test_cloud:
        providers:
            compute: DUMMY
            storage: DUMMY
            dns: DUMMY
        compute_args:
            creds: 4
        storage_args:
            api_key: SECRET KEY
            api_secret: SECRET PASSWORD
        images:
            ubuntu: 1
        sizes:
            medium: 1
        keys:
            testkey: %(pem_file)s
    
roles:
    mailserver:
        key: testkey
        instance:
            image: ubuntu
            size: medium
        min: 1
        max: 3
    appserver:
        key: testkey
        instance:
            image: ubuntu
            size: medium
        min: 1
        max: 1
""" % dict(pem_file = os.path.join(os.path.dirname(__file__), "test_key.pem"))



class TestStateMarshaller(unittest.TestCase):
 
    def _create_cluster(self):
        t = tempfile.NamedTemporaryFile(delete=False)
        t.write(roles1)
        t.close()
        # an empty container
        c = cluster.Cluster("test_cloud",
                            "test_cluster",
                            t.name,
                            )
        return c
    
    def test_load(self):
        c = self._create_cluster()

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
            (0, 'foo', 'fooX'),
            (1, 'bar', 'barX'),
            ]
        output['appserver'] = [(0, 'baz', 'bazX')]
        self.assertEqual(output, dict(cluster.StateMarshaller(c).load(stream)))

    def test_save(self):
        c = self._create_cluster()

        roles = {}
        r = roles['mailserver'] = role.Compute('mailserver', None, None, None)
        r.add_node(0, "foo", "fooX")
        r.add_node(1, "bar", "barX")
        r = roles['appserver'] = role.Compute('appserver', None, None, None)
        r.add_node(0, "baz", "bazX")
        result = yaml.load(cluster.StateMarshaller(c).as_stream(roles.values()))
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

 
