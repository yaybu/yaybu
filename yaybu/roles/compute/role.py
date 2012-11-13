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

import os
import uuid
import logging
import yaml
import StringIO
import datetime
import collections
import time

from libcloud.compute.types import Provider as ComputeProvider
from libcloud.compute.providers import get_driver as get_compute_driver
from libcloud.common.types import LibcloudError
from ssh.ssh_exception import SSHException
from ssh.rsakey import RSAKey
from ssh.dsskey import DSSKey

from .vmware import VMWareDriver
from yaybu.core.util import memoized
from yaybu.core import remote
from yaybu.core.cloud.role import Role
from yaybu.core.cloud import dns
from yaybu.core.util import get_encrypted


logger = logging.getLogger(__name__)


class Compute(Role):

    """ A runtime record of roles we know about. Each role has a list of nodes """
    
    def __init__(self, cluster, name, key_name, image, size, depends=(), dns=None):
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
        self.node = None

        self.key_name = key_name
        self.key = self.get_key()
        self.image = image
        self.size = size
        self.dns = dns

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
        return None
        raise saved_exception

    @property
    @memoized
    def images(self):
        return dict((i.id, i) for i in self.driver.list_images())

    @property
    @memoized
    def sizes(self):
        return dict((s.id, s) for s in self.driver.list_sizes())

    @property
    def nodes(self):
        return dict((n.name, n) for n in self.driver.list_nodes())

    @property
    @memoized
    def driver(self):
        if self.compute_provider == "vmware":
            return VMWareDriver(**self.compute_args)
        provider = getattr(ComputeProvider, self.compute_provider)
        driver_class = get_compute_driver(provider)
        return driver_class(**self.compute_args)

    def role_info(self):
        """ Return the appropriate stanza from the configuration file """
        return self.cluster.ctx.get_config().mapping.get("roles").resolve()[self.name]
            
    def host_info(self):
        """ Return a dictionary of information about this node """
        ## TODO
        ## This needs further work!
        ## the interface names should be extracted properly
        ## and the distro, raid and disks sections should be completed
        n = self.node
        if not n:
            return {}
        def interfaces():
            for i, (pub, priv) in enumerate(zip(n.public_ips, n.private_ips)):
                yield {'name': 'eth%d' % i,
                       'address': priv,
                       'mapped_as': pub}
        return {
            'rolename': self.name,
            'role': copy.copy(self.role_info()),
            'mapped_as': n.public_ips[0],
            'address': n.private_ips[0],
            'hostname': n.extra['dns_name'].split(".")[0],
            'fqdn': n.extra['dns_name'],
            'domain': n.extra['dns_name'].split(".",1)[1],
            'distro': 'TBC',
            'raid': 'TBC',
            'disks': 'TBC',
            'interfaces': list(interfaces()),
        }

    @property
    def hostname(self):
        return self.node.extra['dns_name']

    def context(self):
        """ Creates the context used to provision an actual host """
        ctx = self.cluster.make_context(resume=True)
        ctx.set_host(self.hostname)
        ctx.get_config().load_uri("package://yaybu.recipe/host.yay")
        return ctx

    def create_runner(self):
        """ Create a runner for the specified host, using the key found in
        the configuration """
        r = remote.RemoteRunner(self.hostname, self.key)
        return r

    def install_yaybu(self):
        """ Install yaybu on the provided node.
           Args:
                node: a Node instance
            """
        return self.create_runner().install_yaybu()

    def instantiate(self):
        logger.debug("Node will be %r" % self.full_name)

        """ This creates a physical node based on our node record. """

        if isinstance(self.image, dict):
            image = node.NodeImage(
                id = self.image['id'],
                name = self.image.get('name', self.image['id']),
                ram = self.image.get('extra', {}),
                driver = self.driver,
                )
        else:
            image = self.images.get(self.image, None)

        if isinstance(self.size, dict):
            size = node.NodeSize(
                id = self.size['id'],
                name = self.size.get('name', self.size['id']),
                ram = self.size.get('ram', 0),
                disk = self.size.get('disk', 0),
                bandwidth = self.size.get('bandwidth', 0),
                price = self.size.get('price', 0),
                driver = self.driver,
                )
        else:
            size = self.sizes.get(self.size, None)

        for tries in range(10):
            logger.debug("Creating node %r with image %r, size %r and keypair %r" % (
                name, image, size, keypair))

            node = self.driver.create_node(
                name=name,
                image=image,
                size=image,
                #ex_keyname=keypair
                )

            logger.debug("Waiting for node %r to start" % (name, ))
            ## TODO: wrap this in a try/except block and terminate
            ## and recreate the node if this fails
            try:
                self.driver._wait_until_running(node, timeout=600)
            except LibcloudError:
                logger.warning("Node did not start before timeout. retrying.")
                node.destroy()
                continue
            logger.debug("Node %r running" % (name, ))
            self.node = node

            self.cluster.commit()
            self.node_zone_update(name)
            self.install_yaybu()
            logger.info("Node provisioned: %r" % node)
 
        logger.error("Unable to create node successfully. giving up.")
        raise IOError()

    def decorate_config(self, config):
        if self.cloud is not None:
            new_cfg = {}
            hosts = new_cfg['hosts'] = []
            hosts.append(self.host_info)
            config.add(new_cfg)

    def provision(self, dump=False):
        """ Phase 2 of provisioning """
        for node in self:
            logger.info("Updating host %r" % node)
            if dump:
                host_ctx = node.context()
                self.dump(host_ctx, "%s.yay" % hostname)
            r = self.create_runner()
            result = r.run(self.context())
            if result != 0:
                # stop processing further hosts
                return result

    def destroy(self):
        self.node.destroy()



