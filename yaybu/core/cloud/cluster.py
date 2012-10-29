from __future__ import absolute_import

import StringIO
import datetime
import collections
import yaml
import copy
from yaybu.core import remote, runcontext
from . import api
from . import dependency
from yaybu.core.util import version, get_encrypted

import logging
import abc

from ssh.ssh_exception import SSHException
from ssh.rsakey import RSAKey
from ssh.dsskey import DSSKey

from libcloud.storage.types import ContainerDoesNotExistError, ObjectDoesNotExistError

logger = logging.getLogger(__name__)

class Node:
    
    """ A runtime record we keep of nodes associated with a role. """
    
    def __init__(self, index, name, their_name):
        
        # the index is a number that identifies which node within this role this is
        # for ease of reference (e.g. appserver/0, appserver/1 etc.) these are re-used
        # as required
        self.index = index
        
        # our full name of the node in the form cluster/role/index
        self.name = name
        
        # the unique name assigned by the cloud
        self.their_name = their_name
        
    def __eq__(self, other):
        """ Provided for testability """
        return self.index == other.index and \
               self.name == other.name and \
               self.their_name == other.their_name

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
        
class Role:
    
    """ A runtime record of roles we know about. Each role has a list of nodes """
    
    def __init__(self, name, key_name, key, image, size, depends=(), dns=None, min_=1, max_=1):
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
        self.name = name
        self.key_name = key_name
        self.key = key
        self.image = image
        self.size = size
        self.min = min_
        self.max = max_
        self.depends = depends
        self.dns = dns
        self.nodes = {}
        
    def add_node(self, index, name, their_name):
        self.nodes[index] = Node(index, name, their_name)
        
    def get_node_by_name(self, name):
        """ Return the index and the underlying Node structure """
        for v in self.nodes.values():
            if v.name == name:
                return v
        raise KeyError("Node %r not found" % name)
            
        
    def rm_node(self, their_name):
        for k, v in self.nodes.items():
            if v.their_name == their_name:
                del self.nodes[k]
                return
        raise KeyError("No node found with name %r" % (their_name,))

class StateMarshaller:
    
    """ Abstracts the stored state data. Versioned serialization interface.
    Storage format is YAML with some header information and then a list of
    nodes.
    """
   
    version = 1
    """ The version that will be written when saved. """
    
    @classmethod
    def load(self, data):
        """ Select the appropriate loader based on the version """
        if data is None:
            return {}
        d = yaml.load(data)
        v = d['version']
        loader = getattr(self, "load_%s" % v, None)
        if loader is None:
            raise KeyError("No loader available for state file version %r" % v)
        return loader(d)
    
    @classmethod
    def load_1(self, data):
        """ Returns a dictionary of lists of nodes, indexed by role. For example, 
        {'mailserver': [Node(0, 'cloud/mailserver/0', 'foo'), ...],
         'appserver': [...],
        }  """
        
        nodes = collections.defaultdict(lambda: [])
        for n in data['nodes']:
            nodes[n['role']].append(Node(n['index'], n['name'], n['their_name']))
        return nodes
        
    @classmethod
    def as_stream(self, roles):
        d = {
            'version': self.version,
            'timestamp': str(datetime.datetime.now()),
            'nodes': [],
            }
        for r in roles.values():
            for n in r.nodes.values():
                d['nodes'].append({
                    'role': r.name, 
                    'index': n.index, 
                    'name': n.name, 
                    'their_name': n.their_name,
                })
        return StringIO.StringIO(yaml.dump(d))
    
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

class Cluster:
    
    """ Built on top of AbstractCloud, a Cluster knows about server roles and
    can create and remove nodes for those roles. """
    
    def __init__(self, provider, cluster_name, filename, argv=None, searchpath=(), verbose=True, state_bucket="yaybu-state"):
        """
        Args:
            name: The name of the cloud
            cloud: An AbstractCloud instance
            roles: A list of roles within this cluster
            state_bucket: The name of the bucket used to store the state for clusters
        """
        self.provider = provider
        self.name = cluster_name
        self.filename = filename
        self.searchpath = searchpath
        self.verbose = verbose

        self.cloud = None

        ctx = self.create_initial_context(provider, cluster_name, filename)
        if argv:
            ctx.get_config().set_arguments_from_argv(argv[3:])
        clouds = ctx.get_config().mapping.get('clouds').resolve()
        p = clouds.get(provider, None)
        if p is None:
            raise KeyError("provider %r not found" % provider)
        roles = self.extract_roles(ctx, provider)
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
        self.roles = dict((r.name, r) for r in roles)
        for r in self.roles.values():
            self.cloud.validate(r.image, r.size)
        self.argv = argv
        self.state_bucket = state_bucket
        self.load_state()
        
    def roles_in_order(self):
        """ Return role objects in dependency order """
        graph = dependency.Graph()
        for k, v in self.roles.items():
            for e in v.depends:
                graph.add_edge(k, e)
            else:
                graph.add_node(k)
        for role in graph.resolve():
            yield self.roles[role]
        
    def get_all_hostnames(self):
        """ Return an iterator of all hostnames in this cluster, in order of
        role dependency. """
        for role in self.roles_in_order():
            for node in role.nodes.values():
                # if node.their_name is not found here, it means the 
                # server has died but we still have state.
                n = self.cloud.nodes[node.their_name]
                yield n.extra['dns_name']
                
    def get_all_roles_and_nodenames(self):
        """ Returns an iterator of node names (foo/bar/0) """
        for role in self.roles_in_order():
            for node in role.nodes.values():
                yield role, node.their_name
        
    def get_node_info(self, node):
        """ Return a dictionary of information about the specified node """
        ## TODO
        ## This needs further work!
        ## the interface names should be extracted properly
        ## and the distro, raid and disks sections should be completed
        n = self.cloud.nodes[node.their_name]
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
            
    def load_state(self):
        """ Load the state file from the cloud """
        logger.debug("Loading state from bucket")
        container = self.cloud.get_container(self.state_bucket)
        try:
            bucket = container.get_object(self.name)
            data = "".join(list(bucket.as_stream()))
            nmap = StateMarshaller.load(data)
            for role, nodes in nmap.items():
                api.logger.debug("Finding nodes for role %r" % (role,))
                for n in nodes:
                    self.roles[role].nodes[n.name] = n
            api.logger.debug("State loaded")
        except ObjectDoesNotExistError:
            api.logger.debug("State object does not exist in container")
    
    def store_state(self):
        """ Store the state in the cloud """
        logger.debug("Storing state")
        container = self.cloud.get_container(self.state_bucket)
        ### TODO: fetch it first and check it hasn't changed since we last fetched it
        ### TODO: consider supporting merging in of changes
        container.upload_object_via_stream(StateMarshaller.as_stream(self.roles), 
                                           self.name, {'content_type': 'text/yaml'})

    def provision_roles(self):
        """ Provision nodes for each role up to the minimum required """
        for r in self.roles.values():
            while len(r.nodes) < r.min:
                api.logger.info("Autoprovisioning node for role %r" % r.name)
                node = self.provision_node(r.name)
                api.logger.info("Node provisioned: %r" % node)
                
    def find_lowest_unused(self, role):
        """ Find the lowest unused index for a role. We re-use indexes. """
        index = 0
        for n in sorted(self.roles[role].nodes.keys()):
            if n == index:
                index += 1
        return index
    
    def node_name(self, role, index):
        """ Name a node """
        return "%s/%s/%s" % (self.name, role, index)
    
    def instantiate_node(self, role):
        """ Instantiate a new node for the requested role
        Args:
            role: A Role instance
        """
        index = self.find_lowest_unused(role)
        name = self.node_name(role, index)
        logger.debug("Node will be %r" % name)
        r = self.roles[role]
        node = self.cloud.create_node(name, r.image, r.size, r.key_name)
        r.add_node(index, name, node.name)
        self.store_state()
        self.node_zone_update(role, name)
        return node
        
    def node_zone_update(self, role_name, node_name):
        role = self.roles[role_name]
        if role.dns is None:
            return
        our_node = role.get_node_by_name(node_name)
        zone_info = role.dns.zone_info(our_node.index)
        their_node = self.cloud.nodes[node_name]
        if zone_info is not None:
            self.update_zone(their_node, zone_info[0], zone_info[1])
    
    def destroy_node(self, role, nodename):
        self.cloud.destroy_node(nodename)
        role.rm_node(nodename)
        self.store_state()
    
    def update_zone(self, node, zone, name):
        """ Update the cloud dns to point at the node """
        ip = node.public_ip[0]
        self.cloud.update_record(ip, zone, name)
    
    def install_yaybu(self, node, key):
        """ Install yaybu on the provided node.
        Args:
            node: a Node instance
        """
        rnode = self.cloud.nodes[node.name]
        hostname = rnode.extra['dns_name']
        runner = remote.RemoteRunner(hostname, key)
        runner.install_yaybu()

    def provision(self, dump=False):
        self.provision_roles()
        logger.info("Provisioning completed, updating hosts")
        for hostname in self.get_all_hostnames():
            logger.info("Updating host %r" % hostname)
            host_ctx = self.create_host_context(hostname)
            if dump:
                self.dump(host_ctx, "%s.yay" % hostname)
            result = self.create_runner(host_ctx, hostname).run(host_ctx)
            if result != 0:
                # stop processing further hosts
                return result

    def delete_cloud(self, ctx, provider, cluster_name, filename):
        clouds = ctx.get_config().mapping.get('clouds').resolve()
        p = clouds.get(provider, None)
        if p is None:
            raise KeyError("provider %r not found" % provider)
        raise NotImplementedError

    def provision_node(self, role):
        """ Actually create the node in the cloud. Update our local runtime
        and update the state held in the cloud. """
        node = self.instantiate_node(role)
        key = self.roles[role].key
        self.install_yaybu(node, key)
        return node

    @classmethod
    def get_key(self, ctx, provider, key_name):
        """ Load the key specified by name. """
        clouds = ctx.get_config().mapping.get('clouds').resolve()
        filename = get_encrypted(clouds[provider]['keys'][key_name])
        saved_exception = None
        for pkey_class in (RSAKey, DSSKey):
            try:
                file = ctx.get_file(filename)
                key = pkey_class.from_private_key(file)
                return key
            except SSHException, e:
                saved_exception = e
        raise saved_exception

    @classmethod
    def extract_roles(klass, ctx, provider):
        roles = ctx.get_config().mapping.get('roles').resolve()
        for k, v in roles.items():
            dns = None
            if 'dns' in v:
                zone = get_encrypted(v['dns']['zone'])
                name = get_encrypted(v['dns']['name'])
                dns = SimpleDNSNamingPolicy(zone, name)
            yield Role(
                k,
                get_encrypted(v['key']),
                klass.get_key(ctx, provider, get_encrypted(v['key'])),
                get_encrypted(v['instance']['image']),
                get_encrypted(v['instance']['size']),
                get_encrypted(v.get('depends', ())),
                dns,
                get_encrypted(v.get('min', 0)),
                get_encrypted(v.get('max', None)))

    def host_info(self, info, role_name, role):
        """ Information for a host to be inserted into the configuration.
        Pass an info structure from cloud.get_node_info """
        ## TODO refactor into cloud or an adapter
        hostname = info['fqdn']
        host = copy.copy(info)
        host['role'] = {}
        host['rolename'] = role_name
        for k, v in role.items():
            host['role'][k] = copy.copy(v)
        return host

    def decorate_config(self, ctx):
        """ Update the configuration with the details for all running nodes """
        new_cfg = {'hosts': [],
                   'yaybu': {
                       'provider': self.provider,
                       'cluster': self.name,
                       'argv': {},
                       }
                   }

        ctx.get_config().add(new_cfg)

        if self.cloud is not None:
            roles = ctx.get_config().mapping.get('roles').resolve()
            for role_name, role in self.roles.items():
                for node in role.nodes.values():
                    node_info = self.get_node_info(node)
                    struct = self.host_info(node_info, role_name, roles[role_name])
                    new_cfg['hosts'].append(struct)

        ctx.get_config().add(new_cfg)

    def create_initial_context(self, provider, cluster_name, filename):
        """ Creates a context suitable for instantiating a cloud """
        ctx = runcontext.RunContext(self.filename, ypath=self.searchpath, verbose=self.verbose)
        self.decorate_config(ctx)
        return ctx
    
    def create_host_context(self, hostname):
        """ Creates the context used to provision an actual host """
        ctx = runcontext.RunContext(self.filename, ypath=self.searchpath, verbose=self.verbose, resume=True)
        self.decorate_config(ctx)
        ctx.set_host(hostname)
        if self.argv:
            ctx.get_config().set_arguments_from_argv(self.argv)
        ctx.get_config().load_uri("package://yaybu.recipe/host.yay")
        return ctx

    def create_runner(self, ctx, hostname):
        """ Create a runner for the specified host, using the key found in
        the configuration """
        hosts = ctx.get_config().mapping.get("hosts").resolve()
        host = filter(lambda h: h['fqdn'] == hostname, hosts)[0]
        key_name = host['role']['key']
        key = self.get_key(ctx, self.provider, key_name)
        r = remote.RemoteRunner(hostname, key)
        return r
    
    def dump(self, ctx, filename):
        """ Dump the configuration in a raw form """
        cfg = ctx.get_config().get()
        open(filename, "w").write(yay.dump(cfg))


