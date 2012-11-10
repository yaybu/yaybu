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

from .node import Node
from . import api

from yaybu.core.cloud.role import Role
from yaybu.core.cloud import dns
from yaybu.core.util import get_encrypted

from ssh.ssh_exception import SSHException
from ssh.rsakey import RSAKey
from ssh.dsskey import DSSKey

import logging

logger = logging.getLogger(__name__)


class AbstractCloud:

    """ An abstraction built on top of the libcloud api. Allows you to have
    your own internal names for images and sizes, to increase portability.
    """

    def __init__(self, compute_provider, storage_provider, dns_provider, images, sizes, args=(), compute_args=(), storage_args=()):
        """
        Args:
            compute_provider: The name of the compute provider in libcloud
            storage_provider: the name of the storage provider in libcloud
            dns_provider: The name of the dns provider in libcloud, or 'route53'
            args: A dictionary of arguments to provide to the providers
            images: A dictionary of images that maps your names to the providers names
            sizes: A dictionary of sizes that maps your names to the providers names
        """
        self.cloud = api.Cloud(compute_provider, storage_provider, dns_provider, args, compute_args, storage_args)
        # DUMMY provider has numeric images and sizes
        self.images = dict([(x,str(y)) for (x,y) in images.items()])
        self.sizes = dict([(x,str(y)) for (x,y) in sizes.items()])

    @property
    def nodes(self):
        return self.cloud.nodes

    def get_container(self, name):
        return self.cloud.get_container(name)

    def validate(self, image, size):
        """ Validate that the image and size requested is valid """
        if image not in self.images:
            raise KeyError("Image %r not known" % (image,))

        if size not in self.sizes:
            raise KeyError("Size %r not known" % (size,))

        if self.images[image] not in self.cloud.images:
            raise KeyError("Mapped image %r not known" % (self.images[image], ))

        if self.sizes[size] not in self.cloud.sizes:
            raise KeyError("Mapped size %r not known" % (self.sizes[role.size], ))

    def create_node(self, name, image, size, keypair):
        return self.cloud.create_node(
            name,
            self.images[image],
            self.sizes[size],
            keypair)

    def destroy_node(self, nodename):
        node = self.cloud.nodes[nodename]
        self.cloud.destroy_node(node)

    def update_record(self, ip, zone, name):
        self.cloud.update_record(ip, zone, name)


class Compute(Role):

    """ A runtime record of roles we know about. Each role has a list of nodes """
    
    def __init__(self, cluster, name, key_name, image, size, depends=(), dns=None, min_=1, max_=1):
        """
        Args:
            name: Role name
            key_name: The name of the key at the cloud provider
            key: The key itself as an SSH object
            image: The name of the image in your local dialect
            size: The size of the image in your local dialect
            depends: A list of roles this role depends on
            dns: An instance of DNSNamingPolicy
            min: The minimum number of nodes of this role the cluster should tolerate
            max: The maximum number of nodes of this role the cluster should tolerate
        """
        super(Compute, self).__init__(cluster, name, depends=depends)
        self.provider = "aws-eu-west"

        self.key_name = key_name
        self.key = self.get_key()
        self.image = image
        self.size = size
        self.min = min_
        self.max = max_
        self.dns = dns
        self.nodes = []

        self.create_cloud()

    @classmethod
    def create_from_yay_expression(klass, cluster, name, v):
        np = None
        if 'dns' in v:
            zone = get_encrypted(v['dns']['zone'])
            name = get_encrypted(v['dns']['name'])
            np = dns.SimpleDNSNamingPolicy(zone, name)

        return klass(
                cluster,
                name,
                get_encrypted(v['key']),
                get_encrypted(v['instance']['image']),
                get_encrypted(v['instance']['size']),
                get_encrypted(v.get('depends', ())),
                np,
                get_encrypted(v.get('min', 0)),
                get_encrypted(v.get('max', None)))

    def get_key(self):
        """ Load the key specified by name. """
        cluster = self.cluster
        key_name = self.key_name

        config = cluster.ctx.get_config()
        provider = self.provider

        clouds = config.mapping.get('clouds').resolve()
        filename = get_encrypted(clouds[provider]['keys'][key_name])
        saved_exception = None
        for pkey_class in (RSAKey, DSSKey):
            try:
                file = cluster.ctx.get_file(filename)
                key = pkey_class.from_private_key(file)
                return key
            except SSHException, e:
                saved_exception = e
        raise saved_exception

    def create_cloud(self):
        clouds = self.cluster.ctx.get_config().mapping.get('clouds').resolve()
        p = clouds.get(self.provider, None)
        if p is None:
            raise KeyError("provider %r not found" % self.provider)
        cloud = AbstractCloud(
            get_encrypted(p['providers']['compute']),
            get_encrypted(p['providers']['storage']),
            get_encrypted(p['providers']['dns']),
            get_encrypted(p['images']),
            get_encrypted(p['sizes']),
            args=get_encrypted(p.get('args', {})),
            compute_args=get_encrypted(p.get('compute_args', {})),
            storage_args=get_encrypted(p.get('storage_args', {})),
            )
        self.cloud = cloud
       
    def __iter__(self):
        """ Iterator of nodes. iterates in index order. """
        for n in sorted(self.nodes, key=lambda x: x.index):
            yield n
            
    def role_info(self):
        """ Return the appropriate stanza from the configuration file """
        return self.cluster.ctx.get_config().mapping.get("roles").resolve()[self.name]
        
    def add_node(self, index, name, their_name):
        n = Node(self, index, name, their_name)
        self.nodes.append(n)
        return n

    def get_node_by_our_name(self, name):
        """ Return the index and the underlying Node structure """
        for v in self.nodes:
            if v.name == name:
                return v
        raise KeyError("Node %r not found" % name)
    
    def get_node_by_their_name(self, name):
        for v in self.nodes:
            if v.their_name == name:
                return v
        raise KeyError("Node %r not found" % name)
        
    def rm_node(self, their_name):
        for k, v in self.nodes.items():
            if v.their_name == their_name:
                del self.nodes[k]
                return
        raise KeyError("No node found with name %r" % (their_name,))

    def node_name(self, index):
        """ Name a node """
        return "%s/%s/%s" % (self.cluster.name, self.name, index)

    def instantiate_node(self):
        """ Instantiate a new node for this role  """
        index = self.find_lowest_unused()
        name = self.node_name(index)
        logger.debug("Node will be %r" % name)
        libcloud_node = self.cloud.create_node(name, self.image, self.size, self.key_name)
        node = self.add_node(index, name, libcloud_node.name)
        self.cluster.commit()
        self.node_zone_update(name)
        node.install_yaybu()
        logger.info("Node provisioned: %r" % node)

    def find_lowest_unused(self):
        """ Find the lowest unused index for a role. We re-use indexes for
        nodes that have been and gone. """
        index = 0
        for n in self:
            if n.index == index:
                index += 1
        return index
    
    def instantiate(self):
        """ Instantiate and install nodes for each role up to the minimum required """
        while len(self.nodes) < self.min:
            logger.info("Autoprovisioning node for role %r" % self.name)
            self.instantiate_node()

    def decorate_config(self, config):
        if self.cloud is not None:
            new_cfg = {}
            hosts = new_cfg['hosts'] = []
            for node in self.nodes:
                struct = node.host_info()
                hosts.append(struct)
            config.add(new_cfg)

    def node_zone_update(self, node_name):
        """ Update the DNS, if supported, with the details for this new node """
        if self.dns is None:
            return
        our_node = self.get_node_by_our_name(node_name)
        zone_info = self.dns.zone_info(our_node.index)
        their_node = self.cloud.nodes[node_name]
        if zone_info is not None:
            self.update_zone(their_node, zone_info[0], zone_info[1])

    def update_zone(self, node, zone, name):
        """ Update the cloud dns to point at the node """
        ip = node.public_ip[0]
        self.cloud.update_record(ip, zone, name)
             
    def destroy_node(self, nodename):
        cluster.destroy_node(nodename)
        self.rm_node(nodename)
        self.store_state()
    
    def provision(self, dump=False):
        """ Phase 2 of provisioning """
        for node in self:
            logger.info("Updating host %r" % node)
            if dump:
                host_ctx = node.context()
                self.dump(host_ctx, "%s.yay" % hostname)
            result = node.provision()
            if result != 0:
                # stop processing further hosts
                return result

