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
from yaybu.roles.compute.node import Node

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

class TestAbstractCloud(unittest.TestCase):
    
    def _create_cloud(self):
        cloud = cluster.AbstractCloud(
            'EC2_EU_WEST',
            'S3_EU_WEST',
            'DNS',
            {'ubuntu': 'frob'},
            {'medium': 'nicate'},
            args={},
            )
        cloud.cloud = Mock()
        cloud.cloud.images ={'frob': Mock(id='frob')}
        cloud.cloud.sizes = {'nicate': Mock(id='nicate')}
        return cloud
            
    def test_validate(self):
        cloud = self._create_cloud()
        cloud.validate("ubuntu", "medium")
        self.assertRaises(KeyError, cloud.validate, "ubuntu", "small")
        self.assertRaises(KeyError, cloud.validate, "redhat", "medium")
        self.assertRaises(KeyError, cloud.validate, "ubuntu", "small")
        self.assertRaises(KeyError, cloud.validate, "ubuntu", "small")
    
class TestCluster(unittest.TestCase):
    
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
    
    def test_get_all_hostnames(self):
        c = self._create_cluster()
        c.roles['mailserver'].add_node(0, 'foo', 'server1')
        c.roles['mailserver'].add_node(1, 'bar', 'server2')
        c.roles['appserver'].add_node(0, 'baz', 'server3')
        c.cloud.nodes = {
            'server1': Mock(extra={'dns_name': 'dns1'}),
            'server2': Mock(extra={'dns_name': 'dns2'}),
            'server3': Mock(extra={'dns_name': 'dns3'}),
            }
        self.assertEqual(sorted(c.roles.hostnames()),
                         ['dns1', 'dns2', 'dns3'])
        
    def test_get_node_info(self):
        c = self._create_cluster()
        c.roles['mailserver'].add_node(0, 'foo', 'server1')
        c.cloud.nodes = {
            'server1': Mock(public_ips=['12.12.12.12'],
                            private_ips=['13.13.13.13'],
                            extra={'dns_name': 'dns1.foo.bar'},
                            ),
            }
        self.assertEqual(Node.get_node_info(c.roles['mailserver'].nodes[0]),
                         {'mapped_as': '12.12.12.12',
                          'address': '13.13.13.13',
                          'hostname': 'dns1',
                          'fqdn': 'dns1.foo.bar',
                          'domain': 'foo.bar',
                          'distro': 'TBC',
                          'raid': 'TBC',
                          'disks': 'TBC',
                          'interfaces': [{'name': 'eth0', 
                                          'address': '13.13.13.13', 
                                          'mapped_as': '12.12.12.12',
                                          }],
                          })
        
    def test_find_lowest_unused(self):
        c = self._create_cluster()
        role = c.roles["mailserver"]
        self.assertEqual(role.find_lowest_unused(), 0)
        role.add_node(0, None, None)
        self.assertEqual(role.find_lowest_unused(), 1)
        role.add_node(1, None, None)
        self.assertEqual(role.find_lowest_unused(), 2)
        del role.nodes[1]
        self.assertEqual(role.find_lowest_unused(), 1)

 
