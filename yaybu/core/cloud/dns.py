
import abc

class DNSNamingPolicy(object):
    __metaclass__ = abc.ABCMeta

class SimpleDNSNamingPolicy(DNSNamingPolicy):
    
    """ Provide a name for the first node in a role only """
    
    def __init__(self, zone, name):
        self.zone = zone
        self.name = name
        
    def zone_info(self, index):
        if index == 0:
            return (self.zone, self.name)
        else:
            return None
        

