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

from yaybu.changes import MetadataSync
from yaybu.core.util import memoized
from yaybu.util import args_from_expression
from yaybu import base
from yay import ast, errors
from libcloud.dns.types import Provider as DNSProvider
from libcloud.dns.providers import get_driver as get_dns_driver
from libcloud.common.types import LibcloudError

logger = logging.getLogger(__name__)


class ZoneSync(MetadataSync):

    def __init__(self, expression, driver, zone):
        self.expression = expression
        self.driver = driver
        self.zone = zone

    def get_local_records(self):
        domain = self.expression.domain.as_string().rstrip(".") + "."
        yield domain, dict(
            domain = domain,
            type = self.expression.type.as_string("master"),
            ttl = self.expression.ttl.as_int(0),
            extra = self.expression.extra.as_dict({}),
            )

    def get_remote_records(self):
        if self.zone:
            yield self.zone.domain, dict(
                domain = self.zone.domain,
                type = self.zone.type,
                ttl = self.zone.ttl or 0,
                extra = self.zone.extra,
                )

    def add(self, record):
        self.driver.create_zone(
            domain = record['domain'],
            type = record['type'],
            ttl = record['ttl'],
            extra = record['extra'],
            )

    def update(self, uid, record):
        self.driver.update_zone(
            zone = self.zone,
            domain = record['domain'],
            type = record['type'],
            ttl = record['ttl'],
            extra = record['extra'],
            )

    def delete(self, uid, record):
        self.driver.delete_zone(self.zone)


class RecordSync(MetadataSync):

    def __init__(self, expression, driver, zone):
        self.expression = expression
        self.driver = driver
        self.zone = zone

    def get_local_records(self):
        for rec in self.expression.records:
            # FIXME: Catch error and raise an error with line number information
            type_enum = self.driver._string_to_record_type(rec.type.as_string('A'))

            rid = rec['name'].as_string()
            yield rid, dict(
                name = rec['name'].as_string(),
                type = type_enum,
                data = rec['data'].as_string(),
                extra = rec['extra'].as_dict({'ttl': 10800}),
                )

    def get_remote_records(self):
        if self.zone:
            for rec in self.zone.list_records():
                yield rec.id, dict(
                    name = rec.name,
                    type = rec.type,
                    data = rec.data,
                    extra = rec.extra or {'ttl': 10800},
                    )

    def match_local_to_remote(self, local, remotes):
        for rid, remote in remotes.items():
            if local['name'] != remote['name']:
                continue
            if local['type'] != remote['type']:
                continue

            return rid

    def add(self, record):
        self.driver.create_record(
            name = record['name'],
            zone = self.zone,
            type = record['type'],
            data = record['data'],
            extra = record['extra'],
            )

    def update(self, uid, record):
        self.driver.update_record(
            record = self.driver.get_record(self.zone.id, uid),
            name = record['name'],
            type = record['type'],
            data = record['data'],
            extra = record['extra'],
            )

    def delete(self, uid, record):
        self.driver.update_record(
            record = self.driver.get_record(zone.id, uid),
            )


class Zone(base.GraphExternalAction):

    """
    This part manages a single DNS zone

    new Zone as myzone:
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

    keys = []

    @property
    @memoized
    def driver(self):
        driver_name = self.params.driver.id.as_string()
        Driver = get_dns_driver(getattr(DNSProvider, driver_name))
        driver = Driver(**args_from_expression(Driver, self.params.driver))
        return driver

    def test(self):
        with self.root.ui.throbber("Testing DNS credentials/connectivity") as throbber:
            self.driver.list_zones()

    def apply(self):
        if self.root.readonly:
            return

        driver = self.driver

        domain = self.params.domain.as_string().rstrip(".") + "."
        zones = [z for z in driver.list_zones() if z.domain == domain]

        if len(zones) > 1:
            raise errors.Error("Found multiple zones that match domain name '%s'" % domain)
        elif len(zones) == 1:
            zone = zones[0]
        else:
            zone = None

        zchange = self.root.changelog.apply(
            ZoneSync(
                expression = self.params,
                driver = driver,
                zone = zone,
            ))

        rchange = self.root.changelog.apply(
            RecordSync(
                expression = self.params,
                driver = driver,
                zone = zone,
            ))

        return zchange.changed or rchange.changed
