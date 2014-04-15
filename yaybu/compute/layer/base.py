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

import abc


class Layer(object):
    """ An underlying implementation of a virtualization layer. There is a
    libcloud implementation and a local layer implementation that take quite
    different configuration and have different semantics. """

    __metaclass__ = abc.ABCMeta

    def __init__(self, original):
        self.original = original
        self.their_name = None
        self.node = None  # was libcloud_node

    @property
    def attached(self):
        """ Return True if we have attached to a node. False if we have yet
        to attach to a node. """
        return self.node is not None

    @abc.abstractmethod
    def create(self):
        """ Create a new virtual machine. Do not wait until it is running -
        wait will do that. """

    @abc.abstractmethod
    def wait(self):
        """ Wait a sensible amount of time for a virtual machine created with
        create() to start. attached should return True once the machine is
        running and ready.
        """

    @abc.abstractmethod
    def destroy(self):
        """ Destroy the underlying virtual machine completely. """

    @abc.abstractmethod
    def load(self, name):
        """ Load and start the specified node, if we can find it. """

    @abc.abstractmethod
    def test(self):
        """ Check that we can connect to the underlying driver successfully.
        Raises an exception on failure, otherwise considered to be a success.
        """

    @abc.abstractmethod
    def name(self):
        """ Return a string representing the name of the underlying node. """

    @abc.abstractmethod
    def location(self):
        """ Return a string representing the location of the node, for example it's IP address """

    @abc.abstractproperty
    def public_ip(self):
        """ The primary public IP address of the node """

    @abc.abstractproperty
    def public_ips(self):
        """ A list of all public IP addresses of the node """

    @abc.abstractproperty
    def private_ip(self):
        """ The primary private IP address of the node """

    @abc.abstractproperty
    def private_ips(self):
        """ A list of all private IP addresses of the node """

    @abc.abstractproperty
    def fqdn(self):
        """ The fully qualified domain name of the node """

    @abc.abstractproperty
    def hostname(self):
        """ The unqualified hostname of the node """

    @abc.abstractproperty
    def domain(self):
        """ The domain name of the node """


class LayerException(Exception):
    pass


class NodeFailedToStartException(LayerException):
    pass


class DriverNotFound(LayerException):
    pass
