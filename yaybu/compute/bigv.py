# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
BigV (http://bigv.io) driver.
"""

import base64

try:
    import simplejson as json
except:
    import json

from libcloud.utils.py3 import httplib
from libcloud.utils.py3 import b

from libcloud.common.types import LibcloudError
from libcloud.common.base import JsonResponse, ConnectionUserAndKey
from libcloud.compute.base import is_private_subnet
from libcloud.compute.types import NodeState, InvalidCredsError
from libcloud.compute.base import Node, NodeDriver, NodeImage, NodeSize


LOCATIONS = ['uk0', ]
DEFAULT_LOCATION = LOCATIONS[0]


class BigVResponse(JsonResponse):

    valid_response_codes = [httplib.OK, httplib.ACCEPTED, httplib.CREATED,
                            httplib.NO_CONTENT]

    def parse_error(self):
        if self.status == 401:
            raise InvalidCredsError('Invalid credentials')
        return self.body

    def success(self):
        return self.status in self.valid_response_codes


#=======================================================================
#FIXME: Remove this when there is a better way to do this
from libcloud.common.base import LoggingHTTPSConnection
import socket
import ssl

class BigVHTTPSConnection(LoggingHTTPSConnection):

    def connect(self):
        """Connect

        Checks if verification is toggled; if not, just call
        httplib.HTTPSConnection's connect
        """
        if not self.verify:
            return httplib.HTTPSConnection.connect(self)

        # otherwise, create a connection and verify the hostname
        # use socket.create_connection (in 2.6+) if possible
        if getattr(socket, 'create_connection', None):
            sock = socket.create_connection((self.host, self.port),
                                            self.timeout)
        else:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((self.host, self.port))
        self.sock = ssl.wrap_socket(sock,
                                    self.key_file,
                                    self.cert_file,
                                    cert_reqs=ssl.CERT_REQUIRED,
                                    ca_certs=self.ca_cert,
                                    ssl_version=ssl.PROTOCOL_SSLv3)
        cert = self.sock.getpeercert()
        if not self._verify_hostname(self.host, cert):
            raise ssl.SSLError('Failed to verify hostname')

#=======================================================================


class BigVConnection(ConnectionUserAndKey):

    responseCls = BigVResponse
    conn_classes = (None, BigVHTTPSConnection)

    def add_default_headers(self, headers):
        user_b64 = base64.b64encode(b('%s:%s' % (self.user_id, self.key)))
        headers['Authorization'] = 'Basic %s' % (user_b64.decode('utf-8'))
        headers['Content-Type'] = 'application/json'
        return headers


class BigVNodeDriver(NodeDriver):

    # type = Provider.BIGV
    name = 'BigV'
    website = 'http://bigv.io'
    connectionCls = BigVConnection
    features = {'create_node': ['password']}

    def __init__(self, key, secret, account, group='default', location=DEFAULT_LOCATION, **kwargs):
        """
        @inherits: L{NodeDriver.__init__}

        @keyword    location: Location which should be used
        @type       location: C{str}
        """

        if location not in LOCATIONS:
            msg = 'Invalid location: "%s". Valid locations: %s'
            raise LibcloudError(msg % (location,
                                ', '.join(LOCATIONS)), driver=self)

        super(BigVNodeDriver, self).__init__(key, secret, **kwargs)

        self.account = account
        self.group = group
        self.group_url = '/accounts/%s/groups/%s' % (self.account, self.group)
        self.location = location
        self.connection.host = location + '.bigv.io'

    def list_images(self):
        result = self.connection.request('/definitions').object
        definitions = dict((d['id'], d['data']) for d in result)

        images = []
        for value in definitions['distributions']:
            images.append(NodeImage(id=value, name=value, driver=self.connection.driver, extra={}))

        return images

    def list_sizes(self):
        return [NodeSize(id='default', name='default', ram=1024, disk=5120, bandwidth=0, price=0, driver=self)]

    def list_nodes(self):
        result = self.connection.request(self.group_url+'?view=overview').object

        nodes = []
        for value in result.get('virtual_machines', []):
            node = self._to_node(value)
            nodes.append(node)

        return nodes

    def reboot_node(self, node):
        data = json.dumps({'power_on': False})
        result = self.connection.request(self.group_url+'/virtual_machines/%s' % (node.id),
                                         data=data, method='PUT')

        data = json.dumps({'power_on': True})
        result = self.connection.request(self.group_url+'/virtual_machines/%s' % (node.id),
                                         data=data, method='PUT')

    def destroy_node(self, node):
        result = self.connection.request(self.group_url+'/virtual_machines/%s?purge=true' % (node.id),
                                         method='DELETE')
        return result.status == httplib.NO_CONTENT

    def create_node(self, **kwargs):
        name = kwargs['name']
        size = kwargs['size']
        image = kwargs['image']

        auth = kwargs['auth']

        payload = {
            "reimage": {
                "distribution": image.id,
                "root_password": auth.password,
                "type": "application/vnd.bigv.reimage",
            },
            "discs": [{
                "storage_grade": "sata",
                "size": size.disk,
                "label": "vda",
                "type": "application/vnd.bigv.disc",
            }],
            "virtual_machine": {
                "power_on": True,
                "hardware_profile": None,
                "autoreboot_on": True,
                "cdrom_url": None,
                "memory": size.ram,
                "name": name,
                "cores": "1",
                "type": "application/vnd.bigv.virtual-machine",
            },
            "type": "application/vnd.bigv.vm-create",
        }

        data = json.dumps(payload)
        result = self.connection.request(self.group_url+'/vm_create', data=data,
                                         method='POST')
        return self._to_node(result.object['virtual_machine'])

    def _iter_interfaces(self, id):
        # Structure contains: label, vlan_num, mac, list of ips (including ipv6), extra_ips
        result = self.connection.request(self.group_url+'/virtual_machines/%s/nics' % (id))
        for row in result.object:
            yield row['ips'][0]

    def _to_node(self, data):
        public_ips = []
        private_ips = []

        for ip in self._iter_interfaces(data['id']):
            if is_private_subnet(ip):
                private_ips.append(ip)
            else:
                public_ips.append(ip)

        extra = {
            'management_address': data['management_address'],
            'cores': data['cores'],
            'memory': data['memory'],
            'hostname': data['hostname'],
        }

        if data['power_on'] == True:
            state = NodeState.RUNNING
        elif data['deleted'] == True:
            state = NodeState.TERMINATED
        else:
            state = NodeState.UNKNOWN

        node = Node(id=data['id'], name=data['name'], state=state,
                    public_ips=public_ips, private_ips=private_ips,
                    driver=self.connection.driver, extra=extra)

        return node
