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

from libcloud.compute.base import Node, NodeSize, NodeImage
from libcloud.compute.types import NodeState
from libcloud.compute.drivers.dummy import DummyNodeDriver

from yaybu.compute import Compute
from yaybu.compute.layer.cloud import CloudComputeLayer
from yaybu.compute.layer import base


class MockNodeDriver(DummyNodeDriver):

    # The only change we make to the upstream Dummy driver is to make the state
    # persist between class invocations

    # This allows us to simulate multiple 'yaybu up' invocations with minimal
    # monkey-patching

    nl = []

    def __init__(self, api_key, secret, a=1, b="foo", c=4.5):
        pass

    def create_node(self, **kwargs):
        l = len(self.nl) + 1

        size = kwargs.get('size', NodeSize(
            id='s1',
            name='foo',
            ram=2048,
            disk=160,
            bandwidth=None,
            price=0.0,
            driver=self,
        ))

        image = kwargs.get('image', NodeImage(
            id='i2',
            name='image',
            driver=self,
        ))

        n = Node(id=l,
                 name=kwargs.get('name', 'dummy-%d' % l),
                 state=NodeState.RUNNING,
                 public_ips=['127.0.0.%d' % l],
                 private_ips=[],
                 driver=self,
                 size=size,
                 image=image,
                 extra=kwargs.get('extra', {}),
                 )
        self.nl.append(n)
        return n

    @classmethod
    def install(cls, test_case):
        test_case.addCleanup(setattr, MockNodeDriver, "nl", [])


class MockNodeDriverArgless(MockNodeDriver):

    def __init__(self):
        pass


class MockCloudComputeLayer(CloudComputeLayer):
    def driver_class(self):
        if self.original.driver_id == "DUMMY":
            return MockNodeDriver
        raise base.DriverNotFound


class MockArglessCloudComputeLayer(CloudComputeLayer):
    def driver_class(self):
        return MockNodeDriverArgless

Compute.default_layer = MockCloudComputeLayer
