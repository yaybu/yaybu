
from yaybu.core import remote
from yaybu.core import runcontext
import copy

class Node:

    """ A runtime record we keep of nodes associated with a role. """
    
    def __init__(self, role, index, name, their_name):
        
        self.role = role
        self.cluster = self.role.cluster
        
        # the index is a number that identifies which node within this role this is
        # for ease of reference (e.g. appserver/0, appserver/1 etc.) these are re-used
        # as required
        self.index = index
        
        # our full name of the node in the form cluster/role/index
        self.name = name
        
        # the unique name assigned by the cloud
        self.their_name = their_name
        
    @property
    def lcnode(self):
        """ This fetches the node from the libcloud implementation. This is
        implemented as a property to force it to be refetched when used. """
        return self.cluster.libcloud_nodes[self.their_name]
        
    def get_node_info(self):
        """ Return a dictionary of information about this node """
        ## TODO
        ## This needs further work!
        ## the interface names should be extracted properly
        ## and the distro, raid and disks sections should be completed
        n = self.lcnode
        def interfaces():
            for i, (pub, priv) in enumerate(zip(n.public_ips, n.private_ips)):
                yield {'name': 'eth%d' % i,
                       'address': priv, 
                       'mapped_as': pub}
        return {
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
        return self.lcnode.extra['dns_name']

    def host_info(self):
        """ Information for a host to be inserted into the configuration. """
        info = self.get_node_info()
        hostname = info['fqdn']
        host = copy.copy(info)
        host['rolename'] = self.role.name
        host['role'] = copy.copy(self.role.role_info())
        return host

    def context(self):
        """ Creates the context used to provision an actual host """
        ctx = self.cluster.make_context(resume=True)
        ctx.set_host(self.hostname)
        ctx.get_config().load_uri("package://yaybu.recipe/host.yay")
        return ctx

    def create_runner(self):
        """ Create a runner for the specified host, using the key found in
        the configuration """
        r = remote.RemoteRunner(self.hostname, self.role.key)
        return r
    
    def __eq__(self, other):
        """ Provided for testability """
        return self.index == other.index and \
               self.name == other.name and \
               self.their_name == other.their_name
    
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

