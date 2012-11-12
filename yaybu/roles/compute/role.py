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

from . import api

from yaybu.core.cloud.role import Role
from yaybu.core.cloud import dns
from yaybu.core.util import get_encrypted

from ssh.ssh_exception import SSHException
from ssh.rsakey import RSAKey
from ssh.dsskey import DSSKey

import logging

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

    def create_cloud(self):
        clouds = self.cluster.ctx.get_config().mapping.get('clouds').resolve()
        p = clouds.get(self.provider, None)
        if p is None:
            raise KeyError("provider %r not found" % self.provider)
 
        self.cloud = api.Cloud(
            get_encrypted(p['providers']['compute']),
            get_encrypted(p['providers']['storage']),
            get_encrypted(p['providers']['dns']),
            get_encrypted(p.get('args', {}))
            get_encrypted(p.get('compute_args', {}))
            get_encrypted(p.get('storage_args', {}))
            )
      
    def role_info(self):
        """ Return the appropriate stanza from the configuration file """
        return self.cluster.ctx.get_config().mapping.get("roles").resolve()[self.name]
        
    def instantiate(self):
        logger.debug("Node will be %r" % self.full_name)
        self.node = self.cloud.create_node(self.full_name, self.image, self.size, self.key_name)
        self.cluster.commit()
        self.node_zone_update(name)
        self.install_yaybu()
        logger.info("Node provisioned: %r" % node)

    def decorate_config(self, config):
        if self.cloud is not None:
            new_cfg = {}
            hosts = new_cfg['hosts'] = []
            hosts.append(self.host_info)
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

    def provision(self):
        r = self.create_runner()
        r.run(self.context())

    def install_yaybu(self):
        """ Install yaybu on the provided node.
           Args:
                node: a Node instance
            """
        runner = remote.RemoteRunner(self.hostname, self.role.key)
        runner.install_yaybu()

