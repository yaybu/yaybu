from __future__ import absolute_import

#####################################################################
# Monkeypatch httplib so that libcloud doesn't hang on get_object
# This is only needed on python 2.6 but should be safe for other pythons
# (This fix is now upstream in libcloud, we should dep on it ASAP)
import httplib
HTTPResponse = httplib.HTTPResponse

class HTTPResponse27(HTTPResponse):

    def read(self, amt=None):
        if self.fp is None:
            return ''
        if self._method == 'HEAD':
            self.close()
            return ''
        return HTTPResponse.read(self, amt)

httplib.HTTPResponse = HTTPResponse27
httplib.HTTPConnection.response_class = HTTPResponse27
#####################################################################

import os
import uuid
import logging
import StringIO
import datetime
import collections
import yaml
import copy

from libcloud.storage.types import Provider as StorageProvider
from libcloud.storage.providers import get_driver as get_storage_driver
from libcloud.common.types import LibcloudError
from libcloud.storage.types import ContainerDoesNotExistError, ObjectDoesNotExistError

from yaybu.core.util import memoized


logger = logging.getLogger(__name__)


class StateMarshaller:
    
    """ Abstracts the stored state data. Versioned serialization interface.
    Storage format is YAML with some header information and then a list of
    nodes.
    """
   
    version = 1
    """ The version that will be written when saved. """
    
    def __init__(self, cluster, driver):
        self.cluster = cluster
        self.driver_args = driver_args

    @property
    @memoized
    def driver(self):
        self.driver_name = self.args['id']
        del self.args['id']
        provider = getattr(StorageProvider, self.driver_name)
        driver_class = get_storage_driver(provider)
        return driver_class(**self.driver_args)

    def get_container(self, name):
        try:
            container = self.driver.get_container(container_name=name)
        except ContainerDoesNotExistError:
            container = self.driver.create_container(container_name=name)
        return container

    
    def load(self, data):
        """ Select the appropriate loader based on the version """
        if data is None:
            return {}
        d = yaml.load(data)
        v = d['version']
        loader = getattr(self, "load_%s" % v, None)
        if loader is None:
            raise KeyError("No loader available for state file version %r" % v)
        return loader(d)
    
    def load_1(self, data):
        """ Returns a dictionary of lists of nodes, indexed by role. For example, 
        {'mailserver': [Node(0, 'cloud/mailserver/0', 'foo'), ...],
         'appserver': [...],
        }  """
        
        nodes = collections.defaultdict(lambda: [])
        for n in data['nodes']:
            nodes[n['role']].append((n['index'], n['name'], n['their_name']))
        return nodes
        
    def as_stream(self, roles):
        d = {
            'version': self.version,
            'timestamp': str(datetime.datetime.now()),
            'nodes': [],
            }
        for r in roles:
            for n in r.nodes:
                d['nodes'].append({
                    'role': r.name, 
                    'index': n.index, 
                    'name': n.name, 
                    'their_name': n.their_name,
                })
        return StringIO.StringIO(yaml.dump(d))

    def load_state(self):
        """ Load the state file from the cloud """
        logger.debug("Loading state from bucket")
        container = self.get_container(self.cluster.state_bucket)
        try:
            bucket = container.get_object(self.cluster.name)
            data = "".join(list(bucket.as_stream()))
            nmap = self.load(data)
            for role, nodes in nmap.items():
                logger.debug("Finding nodes for role %r" % (role,))
                for index, name, their_name in nodes:
                    self.cluster.roles[role].add_node(index, name, their_name)
            logger.debug("State loaded")
        except ObjectDoesNotExistError:
            logger.debug("State object does not exist in container")
    
    def store_state(self):
        """ Store the state in the cloud """
        logger.debug("Storing state")
        container = self.get_container(self.cluster.state_bucket)
        ### TODO: fetch it first and check it hasn't changed since we last fetched it
        ### TODO: consider supporting merging in of changes
        container.upload_object_via_stream(self.as_stream(self.cluster.roles), 
                                           self.cluster.name, {'content_type': 'text/yaml'})

 
