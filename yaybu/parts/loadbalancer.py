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

from libcloud.loadbalancer.base import Member, Algorithm
from libcloud.loadbalancer.types import Provider, State
from libcloud.loadbalancer.providers import get_driver
from libcloud.common.types import LibcloudError

logger = logging.getLogger(__name__)


class LoadBalancer(Part):

    """
    This part manages a libcloud load balancer

        parts:
            balancer:
                class: loadbalancer
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

    def __init__(self, cluster, name, config):
        super(LoadBalancer, self).__init__(cluster, name, config)

    @property
    @memoized
    def driver(self):
        config = self.config.get("driver").resolve()
        self.driver_name = config['id']
        del config['id']
        driver = getattr(Provider, self.driver_name)
        driver_class = get_driver(driver)
        return driver_class(**self.config)

    def instantiate(self):
        pass

    def provision(self):
        pass

