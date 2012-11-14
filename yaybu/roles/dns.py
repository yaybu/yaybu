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


from __future__ import absolute_import

import os
import uuid
import logging
import yaml
import StringIO
import datetime
import collections
import time

from yaybu.core.cloud.role import Role
from yaybu.core.error import ArgParseError
from yaybu.core.util import memoized

from libcloud.dns.types import Provider as DNSProvider
from libcloud.dns.providers import get_driver as get_dns_driver
from libcloud.common.types import LibcloudError

import libcloud.security
libcloud.security.VERIFY_SSL_CERT = False
libcloud.security.VERIFY_SSL_CERT_STRICT = False

from boto.route53.exception import DNSServerError
from boto.route53.connection import Route53Connection
from boto.route53.record import ResourceRecordSets
from boto.route53.record import Record

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


class Zone(Role):

    """
    This role manages a single DNS zone

        roles:
            mydns:
                class: zone
                driver:
                    id: AWS
                    key:
                    secret:
                domain: example.com
                type: master
                ttl: 60
                records:
                  - name: www
                    type: A
                    data: 192.168.1.1
    """

    def __init__(self, cluster, name, config):
        super(Zone, self).__init__(cluster, name)
        self.config = config

    @classmethod
    def create_from_yay_expression(klass, cluster, name, args):
        return klass(cluster, name, args)

    @property
    @memoized
    def driver(self):
        if self.dns_provider == "route53":
            return Route53(**self.args)
        else:
            driver = getattr(DNSProvider, self.driver_name)
            driver_class = get_dns_driver(driver)
            return driver_class(**self.args)

    def update_record(self, ip, zone, name):
        """ Create an A record for the ip/dns pairing """
        fqdn = "%s.%s." % (name, zone)
        z = self.dns.create_zone(domain=zone)
        record = z.create_record(name=fqdn, data=ip)
        logger.info("Created record for %r -> %r" % (name, ip))

    def instantiate(self):
        pass

    def decorate_config(self, config):
        pass

    def provision(self):
        simulate = self.context().simulate
        params = self.role_info()

        retval = False
        zone = None

        zones = [z for z in self.driver.list_zones() if z.domain == self.domain]
        if len(zones):
            zone = zones[0]
            changed = False
            if self.type_ != zone.type:
                changed = True
            if self.ttl != zone.ttl:
                changed = True
            if self.extra != zone.extra:
                changed = True
            if changed:
                logger.info("Updating %s" % self.domain)
                if not simulate:
                    zone.update(self.domain, self.type_, self.ttl, self.extra)
                retval = True
        else:
            logger.info("Creating %s (type=%s, ttl=%s, extra=%r)" % (self.domain, self.type_, self.ttl, self.extra))
            if not simulate:
                zone = self.driver.create_zone(self.domain, self.type_, self.ttl, self.extra)
            retval = True

        if not zone and simulate:
            all_records = []
        else:
            all_records = zone.list_records()

        for rec in self.records:
            type_ = self.driver._string_to_record_type(rec['type'])
            found = [m for m in all_records if m.type == type_ and m.name == rec['name']]
            if len(found):
                r = found[0]
                changed = False
                if rec['ttl'] != r.ttl:
                    changed = True
                if rec.get('extra', {}) != r.extra:
                    changed = True
                if changed:
                    logger.info("Updating %s" % rec['name'])
                    if not simulate:
                        r.update(rec['name'], type_, rec['ttl'], rec.get('extra', {}))
                    retval = True
            else:
                logger.info("Creating %s (type=%s, ttl=%s, extra=%r)" % (rec['name'], rec['type'], rec['ttl'], rec.get('extra', {})))
                if not simulate:
                    zone.create_record(rec['name'], rec['type'], rec['ttl'], rec.get('extra', {}))
                retval = True

        return retval

