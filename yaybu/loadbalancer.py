# Copyright 2013 Isotoma Limited
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

from yaybu.core.util import memoized
from yaybu.core.state import PartState
from yaybu.util import args_from_expression
from yaybu import base
from libcloud.loadbalancer.base import Member, Algorithm
from libcloud.loadbalancer.types import Provider, State
from libcloud.loadbalancer.providers import get_driver

from yaybu.changes import MetadataSync


logger = logging.getLogger(__name__)


class SyncMembers(MetadataSync):

    def __init__(self, expression, driver, balancer):
        self.expression = expression = expression
        self.driver = driver
        self.balancer = balancer

    def get_local_records(self):
        for m in self.expression:
            id = m.id.as_string()
            yield id, dict(
                id = m.id.as_string(default='') or None,
                ip = m.ip.as_string(default='') or None,
                port = m.port.as_int(default=0) or None,
                )

    def get_remote_records(self):
        if not self.balancer:
            raise StopIteration

        for m in self.balancer.list_members():
            yield m.id, dict(
                id = m.id,
                ip = m.ip,
                port = m.port,
                )

    def add(self, record):
        self.balancer.attach_member(Member(
            id = record['id'],
            ip = record['ip'],
            port = record['port'],
            ))

    def update(self, record):
        self.delete(record)
        self.add(record)

    def delete(self, uid, record):
        self.balancer.detach_member(Member(
            id = record['id'],
            ip = record['ip'],
            port = record['port'],
            ))


class LoadBalancer(base.GraphExternalAction):

    """
    This part manages a libcloud load balancer

        new LoadBalancer as mylb:
            name: mylb

            driver:
                id: AWS
                key:
                secret:

            port: 80
            protocol: http
            algorithm: round-robin

            members:
              - id: {{webnode.id}}
                ip: {{webnode.public_ip}}
                port: 8080

    Algorithm must be one of:
        random
        round-robin
        least-connections
        weighted-round-robin
        weighted-least-connections

    """

    extra_drivers = {}

    keys = []

    @property
    @memoized
    def state(self):
        return PartState(self.root.state, self.params.name.as_string())

    @property
    @memoized
    def driver(self):
        driver_id = self.params.driver.id.as_string()
        if driver_id in self.extra_drivers:
            Driver = self.extra_drivers[driver_id]
        else:
            Driver = get_driver(getattr(Provider, driver_id))

        driver = Driver(**args_from_expression(Driver, self.params.driver))
        return driver

    def _find_balancer(self):
        if "balancer_id" in self.state:
            try:
                return self.driver.get_balancer(self.state["balancer_id"])
            except:
                return None
        else:
            for balancer in self.driver.list_balancers():
                if balancer.name == self.params.name.as_string():
                    return balancer

    def apply(self):
        if self.root.readonly:
            return

        self.state.refresh()

        default_algorithm = self.driver.list_supported_algorithms()[0]
        default_protocol = self.driver.list_protocols()[0]

        name = self.params.name.as_string()
        port = self.params.port.as_int()
        protocol = self.params.protocol.as_string()
        algorithm = self.params.algorithm.as_string()

        lb = self._find_balancer()
        changed = False

        if not lb:
            with self.root.ui.throbber("Creating load balancer '%s'" % name) as throbber:
                if not self.root.simulate:
                    lb = self.driver.create_balancer(
                        name = name,
                        port = port,
                        protocol = protocol,
                        algorithm = algorithm,
                        members = [],
                        )
                else:
                    lb = None
                changed = True
                self.root.changelog.changed = True

        else:
            if lb.name != name:
                print "Requested name %s, current name %s" % (name, lb.name)
                changed = True
            if lb.port != port:
                print "Requested port %s, current port %s" % (port, lb.port)
                changed = True
            #if lb.protocol != protocol:
            #    changed = True
            #if lb.algorithm != algorithm:
            #    changed = True

            if changed:
                with self.root.ui.throbber("Updating load balancer '%s'" % name) as throbber:
                    if not self.root.simulate:
                        self.driver.update_balancer(
                            balancer = lb,
                            name = name,
                            port = port,
                            protocol = protocol,
                            algorithm = algorithm,
                            )
                    self.root.changelog.changed = True

        self.root.changelog.apply(
            SyncMembers(
                expression = self.params.members,
                driver = self.driver,
                balancer = lb,
                ))

        if lb:
            self.state.update(balancer_id=lb.id)

        return changed

    def destroy(self):
        balancer = self._find_balancer()
        if not balancer:
            return
        with self.root.ui.throbber("Destroying load balancer '%s'" % balancer.name) as throbber:
            balancer.destroy()

