
import unittest
from mock import MagicMock as Mock
from StringIO import StringIO
import yaml
from yaybu.core.cloud import cluster
from libcloud.storage.types import ContainerDoesNotExistError, ObjectDoesNotExistError

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

class TestAbstractCloud(unittest.TestCase):
    
    def _create_cloud(self):
        cloud = cluster.AbstractCloud(
            'EC2_EU_WEST',
            'S3_EU_WEST',
            'DNS',
            {},
            {'ubuntu': 'frob'},
            {'medium': 'nicate'},
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
        roles = [
            cluster.Role("mailserver",
                         "fookey",
                         None,
                         "ubuntu",
                         "medium",
                         min_=1,max_=3),
            cluster.Role("appserver",
                         "fookey",
                         None,
                         "ubuntu",
                         "medium",
                         min_=1,max_=1)
            ]
        cloud = Mock()
        cloud.validate = Mock(return_value=None)
        # an empty container
        container = Mock()
        container.get_object = Mock()
        container.get_object.side_effect = ObjectDoesNotExistError(None, None, None)
        cloud.get_container = Mock(return_value=container)
        c = cluster.Cluster(cloud,
                            "test_cluster",
                            roles,
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
        self.assertEqual(sorted(c.get_all_hostnames()),
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
        self.assertEqual(c.get_node_info(c.roles['mailserver'].nodes[0]),
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
        self.assertEqual(c.find_lowest_unused("mailserver"), 0)
        c.roles["mailserver"].add_node(0, None, None)
        self.assertEqual(c.find_lowest_unused("mailserver"), 1)
        c.roles["mailserver"].add_node(1, None, None)
        self.assertEqual(c.find_lowest_unused("mailserver"), 2)
        del c.roles["mailserver"].nodes[1]
        self.assertEqual(c.find_lowest_unused("mailserver"), 1)
        
    
        
                         
        
        
        
        
        
        
        
                         
