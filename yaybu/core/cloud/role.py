from __future__ import absolute_import

from . import dependency

from yaybu.core.util import get_encrypted
from yay.errors import NoMatching

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
    
    def __init__(self, ctx):
        self.ctx = ctx
        self.config = ctx.get_config()
        
    def create_collection(self, cluster):
        c = RoleCollection()
        for k in self.config.mapping.get('roles').keys():
            v = self.config.mapping.get('roles').get(k)
            try:
                classname = get_encrypted(v.get("class").resolve())
            except NoMatching:
                classname = "compute"

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
    
    def __init__(self, cluster, name, depends=()):
        """
        Args:
            name: Role name
            depends: A list of roles this role depends on
        """
        self.name = name
        self.depends = depends
        self.cluster = cluster
    
    def context(self):
        ctx = self.cluster.make_context(resume=True)
        return ctx
    
    def role_info(self):
        """ Return the appropriate stanza from the configuration file """
        return self.cluster.ctx.get_config().mapping.get("roles").resolve()[self.name]
   
    def instantiate(self):
        raise NotImplementedError

    def decorate_config(self, config):
        pass
 
    def provision(self, dump=False):
        raise NotImplementedError

