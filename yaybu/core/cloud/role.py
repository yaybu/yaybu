
from . import dependency
from . import dns

from yaybu.core.util import get_encrypted

from ssh.ssh_exception import SSHException
from ssh.rsakey import RSAKey
from ssh.dsskey import DSSKey

import logging

logger = logging.getLogger(__name__)

from abc import ABCMeta, abstractmethod, abstractproperty

class RoleType(ABCMeta):

    """ Registers the provider with the resource which it provides """

    types = {}

    def __new__(meta, class_name, bases, new_attrs):
        cls = super(RoleType, meta).__new__(meta, class_name, bases, new_attrs)
        meta.types[new_attrs.get("rolename", class_name.lower())] = cls
        return cls


## Should this just be class methods on RoleCollection?
class RoleCollectionFactory(object):
    
    """ Parses role and cloud details from a configuration and creates a
    RoleCollection based on it. """
    
    def __init__(self, ctx, provider):
        self.ctx = ctx
        self.provider = provider
        self.config = ctx.get_config()
        
    def create_collection(self, cluster):
        c = RoleCollection()
        roles = self.config.mapping.get('roles').resolve()
        for k, v in roles.items():
            classname = get_encrypted(v.get("class", "compute"))
            r = RoleType.types[classname].create_from_yay_expression(cluster, k, v)
            c.add_role(r)
        return c
        

class RoleCollection(object):
    
    """ A representation of a directed graph of roles. """
    
    def __init__(self):
        self.__roles = {}
        
    def add_role(self, role):
        self.__roles[role.name] = role
        
    def __getitem__(self, name):
        return self.__roles[name]

    def __iter__(self):
        """ Return role objects in dependency order """
        graph = dependency.Graph()
        for k, v in self.__roles.items():
            for e in v.depends:
                graph.add_edge(k, e)
            else:
                graph.add_node(k)
        for role in graph.resolve():
            yield self.__roles[role]
        
    def hostnames(self):
        """ Return an iterator of all hostnames in this cluster, in order of
        role dependency. """
        for role in self:
            for node in role.nodes:
                yield node.hostname
            
    def get_all_roles_and_nodenames(self):
        """ Returns an iterator of node names (foo/bar/0) """
        for role in role.RoleCollection.roles():
            for node in role.nodes.values():
                yield role, node.their_name
    
    def provision(self, dump=False):
        """ Provision everything in two phases. In the first phase, nodes are
        instantiated in the cloud and have yaybu installed on them (as
        required). In the second phase the configuration is applied to each
        node in turn, with all configuration information available for the
        entire cluster. """
        for r in self:
            r.instantiate()
        logger.info("Provisioning completed, updating hosts")
        for r in self:
            r.provision()


class Role(object):

    __metaclass__ = RoleType

    """ A runtime record of roles we know about. Each role has a list of nodes """
    
    def __init__(self, cluster, name, depends=(), dns=None):
        """
        Args:
            name: Role name
            depends: A list of roles this role depends on
            dns: An instance of DNSNamingPolicy
        """
        self.name = name
        self.depends = depends
        self.dns = dns
        self.cluster = cluster
        
    def role_info(self):
        """ Return the appropriate stanza from the configuration file """
        return self.cluster.ctx.get_config().mapping.get("roles").resolve()[self.name]
        
    def instantiate(self):
        """ Instantiate and install nodes for each role up to the minimum required """
        while len(self.nodes) < self.min:
            logger.info("Autoprovisioning node for role %r" % self.name)
            self.instantiate_node()
    
    def node_zone_update(self, node_name):
        """ Update the DNS, if supported, with the details for this new node """
        if self.dns is None:
            return
        our_node = self.get_node_by_our_name(node_name)
        zone_info = self.dns.zone_info(our_node.index)
        their_node = self.cluster.libcloud_nodes[node_name]
        if zone_info is not None:
            self.update_zone(their_node, zone_info[0], zone_info[1])

    def update_zone(self, node, zone, name):
        """ Update the cloud dns to point at the node """
        ip = node.public_ip[0]
        self.cluster.cloud.update_record(ip, zone, name)
             
    def provision(self, dump=False):
        raise NotImplementedError

