# Copyright 2012 Isotoma Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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

import libcloud.security
libcloud.security.VERIFY_SSL_CERT = False
libcloud.security.VERIFY_SSL_CERT_STRICT = False

from libcloud.compute.types import Provider as ComputeProvider
from libcloud.storage.types import Provider as StorageProvider
from libcloud.dns.types import Provider as DNSProvider

from libcloud.compute.providers import get_driver as get_compute_driver
from libcloud.storage.providers import get_driver as get_storage_driver
from libcloud.dns.providers import get_driver as get_dns_driver

from libcloud.common.types import LibcloudError
from libcloud.storage.types import ContainerDoesNotExistError

from .vmware import VMWareDriver

from boto.route53.exception import DNSServerError
from boto.route53.connection import Route53Connection
from boto.route53.record import ResourceRecordSets
from boto.route53.record import Record

import os
import uuid
import logging
import yaml
import StringIO
import datetime
import collections
import time

from yaybu.core.util import memoized
from yaybu.core import remote

logger = logging.getLogger(__name__)

max_version = 1

class Route53Zone:
    
    def __init__(self, connection, zone):
        self.connection = connection
        self.id = zone['Id'].replace('/hostedzone/', '')
        
    def get_record(self, name):
        records = self.connection.get_all_rrsets(self.id, type=None)
        for record in records:
            if record.name == name:
                return record
        
    def create_record(self, name, data):
        """ Note that the name should be a dot terminated FQDN! """
        assert isinstance(self.connection, Route53Connection)
        record = self.get_record(name)
        changes = ResourceRecordSets(self.connection, self.id, "")
        if record:
            changes.add_change("DELETE", name, 'A', 60).add_value(record.resource_records[0])
        changes.add_change("CREATE", name, 'A', 60).add_value(data)
        status = changes.commit()['ChangeResourceRecordSetsResponse']['ChangeInfo']
        logger.debug("Status response is %r" % status)
            
        
class Route53:
    
    """ Our driver that handles route53 using boto """
    
    def __init__(self, key, secret):
        self.connection = Route53Connection(key, secret)
        
    def create_zone(self, domain):
        """" Create the zone if it does not exist """
        zone = self.connection.get_hosted_zone_by_name(domain)
        if zone is None:
            zone = self.connection.create_hosted_zone(domain)
            logger.debug("Created zone %r" % domain)
            zone = zone['CreateHostedZoneResponse']['HostedZone']
            return Route53Zone(self.connection, zone)  
        else:
            zone = zone['GetHostedZoneResponse']['HostedZone']
            return Route53Zone(self.connection, zone)

class Cloud(object):

    """ Adapter of a cloud that provides access to runtime functionality. """

    def __init__(self, storage_provider, dns_provider, args=(), storage_args=()):
        """ storage_args and compute_args will be used for preference if
        provided. otherwise args are used for both """
        self.storage_provider = storage_provider
        self.dns_provider = dns_provider
        self.args = dict(args)
        self.storage_args = dict(storage_args) or self.args
    
    @property
    @memoized
    def storage(self):
        provider = getattr(StorageProvider, self.storage_provider)
        driver_class = get_storage_driver(provider)
        return driver_class(**self.storage_args)
    
    @property
    @memoized
    def dns(self):
        if self.dns_provider == "route53":
            return Route53(**self.args)
        else:
            provider = getattr(DNSProvider, self.dns_provider)
            driver_class = get_dns_driver(provider)
            return driver_class(**self.args)

    def get_container(self, name):
        try:
            container = self.storage.get_container(container_name=name)
        except ContainerDoesNotExistError:
            container = self.storage.create_container(container_name=name)
        return container

    def update_record(self, ip, zone, name):
        """ Create an A record for the ip/dns pairing """
        fqdn = "%s.%s." % (name, zone)
        z = self.dns.create_zone(domain=zone)
        record = z.create_record(name=fqdn, data=ip)
        logger.info("Created record for %r -> %r" % (name, ip))
        
