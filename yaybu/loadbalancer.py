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

from yaybu.core.util import memoized
from yaybu import base
from yay import errors
from libcloud.loadbalancer.base import Member, Algorithm
from libcloud.loadbalancer.types import Provider, State
from libcloud.loadbalancer.providers import get_driver
from libcloud.common.types import LibcloudError

logger = logging.getLogger(__name__)


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

    keys = []

    @property
    @memoized
    def driver(self):
        config = self["driver"].as_dict()
        self.driver_name = config['id']
        del config['id']
        driver = getattr(Provider, self.driver_name)
        driver_class = get_driver(driver)
        return driver_class(**config)

    def apply(self):
        if self.root.readonly:
            return

        self.state.refresh()

        default_algorithm = self.driver.list_supported_algorithms()[0]
        default_protocol = self.driver.list_protocols()[0]

        name = self.params.name.as_string()
        port = self.params.port.as_integer()
        protocol = self.params.protocol.as_string()
        algorithm = self.params.algorithm.as_string()

        lb = None

        if "balancer_id" in self.state:
            lb = self.driver.get_balancer(self.state["balancer_id"])
        else:
            for balancer in self.driver.list_balancers(self):
                if balancer.name == self.params.name.as_string():
                    self.state.update(balancer_id=balancer.id)
                    lb = balancer

        changed = False

        if not lb:
            with self.root.ui.throbber("Creating load balancer '%s'" % name) as throbber:
                lb = self.driver.create_balancer(
                    name = name,
                    port = port,
                    protocol = protocol,
                    algorithm = algorithm,
                    members = [],
                    )
                changed = True

        else:
            if balancer.name != name:
                changed = True
            if balancer.port != port:
                changed = True
            if balancer.protocol != protocol:
                changed = True
            if balancer.algorithm != algorithm:
                changed = True

            with self.root.ui.throbber("Updating load balancer '%s'" % name) as throbber:
                self.driver.update_balancer(
                    balancer = lb,
                    name = name,
                    port = port,
                    protocol = protocol,
                    algorithm = algorithm,
                    )

        return changed
