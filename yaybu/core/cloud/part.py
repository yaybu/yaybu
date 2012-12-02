from __future__ import absolute_import

from . import dependency

from yaybu.core.util import memoized, get_encrypted
from yay.errors import NoMatching

import logging

logger = logging.getLogger(__name__)

from abc import ABCMeta, abstractmethod, abstractproperty

class PartType(ABCMeta):

    """ Registers the provider with the resource which it provides """

    types = {}

    def __new__(meta, class_name, bases, new_attrs):
        cls = super(PartType, meta).__new__(meta, class_name, bases, new_attrs)
        meta.types[new_attrs.get("partname", class_name.lower())] = cls
        return cls


## Should this just be class methods on PartCollection?
class PartCollectionFactory(object):
    
    """ Parses part and cloud details from a configuration and creates a
    PartCollection based on it. """
    
    def __init__(self, ctx):
        self.ctx = ctx
        self.config = ctx.get_config()
        
    def create_collection(self, cluster):
        c = PartCollection()
        for k in self.config.mapping.get('parts').keys():
            v = self.config.mapping.get('parts').get(k)
            try:
                classname = get_encrypted(v.get("class").resolve())
            except NoMatching:
                classname = "compute"

            r = PartType.types[classname](cluster, k, v)
            c.add_part(r)
        return c
        

class PartCollection(object):
    
    """ A representation of a directed graph of parts. """
    
    def __init__(self):
        self.__parts = {}
        
    def add_part(self, part):
        self.__parts[part.name] = part
        
    def __getitem__(self, name):
        return self.__parts[name]

    def __iter__(self):
        """ Return part objects in dependency order """
        graph = dependency.Graph()
        for k, v in self.__parts.items():
            for e in v.depends:
                graph.add_edge(k, e)
            else:
                graph.add_node(k)
        for part in graph.resolve():
            yield self.__parts[part]
        

class Part(object):

    __metaclass__ = PartType

    """ A runtime record of parts we know about. Each part has a list of nodes """
    
    def __init__(self, cluster, name, config):
        """
        Args:
            name: Part name
            depends: A list of parts this part depends on
        """
        self.name = name
        self.cluster = cluster
        try:
            self.depends = config.get('depends')
        #except NoMatching:
        except:
            self.depends = ()

    def set_state(self, state):
        pass

    def get_state(self):
        return {}
 
    @property
    @memoized
    def ctx(self):
        return self.cluster.make_context(resume=True)

    @property
    @memoized
    def fullconfig(self):
        return self.ctx.get_config()
 
    @property
    def config(self):
        return self.fullconfig.mapping.get("parts").get(self.name)

    def get_part_info(self):
        """ Return the appropriate stanza from the configuration file """
        #return self.config.mapping.get("parts").resolve()[self.name]
        return {}

    def set_parts_info(self, info):
        return self.fullconfig.add({
            "parts": info,
            })
   
    def instantiate(self):
        raise NotImplementedError

    def provision(self, dump=False):
        raise NotImplementedError

