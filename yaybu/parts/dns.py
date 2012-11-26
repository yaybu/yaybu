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

import logging

from yaybu.core.cloud.part import Part
from yaybu.core.error import ArgParseError
from yaybu.core.util import memoized

from libcloud.dns.types import Provider as DNSProvider
from libcloud.dns.providers import get_driver as get_dns_driver
from libcloud.common.types import LibcloudError

from .route53 import Route53DNSDriver

logger = logging.getLogger(__name__)


class Zone(Part):

    """
    This part manages a single DNS zone

        parts:
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
        config = self.config.get("driver").resolve()
        self.driver_name = config['id']
        del config['id']
        if self.driver_name == "route53":
            return Route53DNSDriver(**config)
        else:
            driver = getattr(DNSProvider, self.driver_name)
            driver_class = get_dns_driver(driver)
            return driver_class(**self.config)

    def instantiate(self):
        pass

    def decorate_config(self, config):
        pass

    def provision(self):
        simulate = self.context().simulate
        params = self.part_info()

        domain = params['domain'].rstrip(".") + "."
        ttl = params.get('ttl', 0)
        type_ = params.get('type', 'master')
        extra = params.get('extra', {})

        retval = False
        zone = None

        print [z for z in self.driver.list_zones()]
        zones = [z for z in self.driver.list_zones() if z.domain == domain]
        if len(zones):
            zone = zones[0]
            changed = False
            if type_ != zone.type:
                changed = True
            if ttl != zone.ttl:
                changed = True
            if extra != zone.extra:
                changed = True
            if changed:
                logger.info("Updating %s" % domain)
                if not simulate:
                    zone.update(domain, type_, ttl, extra)
                retval = True
        else:
            logger.info("Creating %s (type=%s, ttl=%s, extra=%r)" % (domain, type_, ttl, extra))
            if not simulate:
                zone = self.driver.create_zone(domain, type_, ttl, extra)
            retval = True

        if not zone and simulate:
            all_records = []
        else:
            all_records = zone.list_records()

        for rec in params.get('records', []):
            type_str = rec.get('type', 'A')
            type_enum = self.driver._string_to_record_type(type_str)
            ttl = rec.get('ttl', 0)

            found = [m for m in all_records if m.type == type_ and m.name == rec['name']]
            if len(found):
                r = found[0]
                changed = False
                if ttl != r.ttl:
                    changed = True
                if rec.get('extra', {}) != r.extra:
                    changed = True
                if changed:
                    logger.info("Updating %s" % rec['name'])
                    if not simulate:
                        r.update(rec['name'], type_str, ttl, rec.get('extra', {}))
                    retval = True
            else:
                logger.info("Creating %s.%s (type=%s, ttl=%s, extra=%r)" % (rec['name'], domain, type_str, ttl, rec.get('extra', {})))
                if not simulate:
                    zone.create_record(rec['name'], type_enum, rec['data'], rec.get('extra', {}))
                retval = True

        return retval

