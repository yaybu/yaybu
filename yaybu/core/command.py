
""" Provides command-driven input to yaybu, using cmd.Cmd """

import os
import cmd
import optparse
import copy
import logging
from functools import partial

import yay
import yay.errors
from yaybu.core import runner, remote, runcontext, error
from yaybu.core.util import version, get_encrypted
from yaybu.core.cloud.cluster import Cluster, Role
from ssh.ssh_exception import SSHException
from yaybu.core.cloud.cluster import Cluster, AbstractCloud, SimpleDNSNamingPolicy

from ssh.rsakey import RSAKey
from ssh.dsskey import DSSKey

logger = logging.getLogger("yaybu.core.command")

class YaybuArgParsingError(Exception):
    pass

class YaybuArg:
    
    def __init__(self, name, type_='string', default=None, help=None):
        self.name = name.lower()
        self.type = type_.lower()
        self.default = default
        self.help = help
        self.value = None
        
    def set(self, value):
        self.value = value
        
    def _get(self):
        if self.value is None and self.default is not None:
            return self.default
        else:
            return self.value
        
    def get(self):
        return self.convert(self._get())
    
    def convert(self, value):
        if self.type == 'string':
            return value
        elif self.type == 'integer':
            try:
                return int(value)
            except ValueError:
                raise YaybuArgParsingError("Cannot convert %r to an int for argument %r" % (value, self.name))
        elif self.type == 'boolean':
            if type(value) == type(True):
                # might already be boolean
                return value
            if value.lower() in ('no', '0', 'off', 'false'):
                return False
            elif value.lower() in ('yes', '1', 'on', 'true'):
                return True
            raise YaybuArgParsingError("Cannot parse boolean from %r for argument %r" % (value, self.name))
        else:
            raise YaybuArgParsingError("Don't understand %r as a type for argument %r" % (self.type, self.name))
        
class YaybuArgParser:
    
    def __init__(self, *args):
        self.args = {}
        for a in args:
            self.add(a)
        
    def add(self, arg):
        if arg.name in self.args:
            raise YaybuArgParsingError("Duplicate argument %r specified" % (arg.name,))
        self.args[arg.name] = arg
        
    def parse(self, argv):
        for arg in argv:
            name, value = arg.split("=", 1)
            if name not in self.args:
                raise YaybuArgParsingError("Unexpected argument %r provided on command line" % (name,))
            self.args[name].set(value)
        return dict(self.values())
    
    def values(self):
        for a in self.args.values():
            yield (a.name, a.get())

class OptionParsingCmd(cmd.Cmd):
    
    def parser(self):
        p = optparse.OptionParser(usage="")
        p.remove_option("-h")
        return p

    def onecmd(self, line):
        """Interpret the argument as though it had been typed in response
        to the prompt.

        This may be overridden, but should not normally need to be;
        see the precmd() and postcmd() methods for useful execution hooks.
        The return value is a flag indicating whether interpretation of
        commands by the interpreter should stop.

        """
        cmd, arg, line = self.parseline(line)
        if not line:
            return self.emptyline()
        if cmd is None:
            return self.default(line)
        self.lastcmd = line
        if line == 'EOF' :
            self.lastcmd = ''
        if cmd == '':
            return self.default(line)
        else:
            try:
                func = getattr(self, 'do_' + cmd)
            except AttributeError:
                return self.default(line)
            parser = self.parser()
            optparse_func = getattr(self, 'opts_' + cmd, lambda x: x)
            optparse_func(parser)
            opts, args = parser.parse_args(arg.split())
            return func(opts, args)
        
    def aligned_docstring(self, arg):
        """ Return a docstring for a function, aligned properly to the left """
        try:
            doc=getattr(self, 'do_' + arg).__doc__
            if doc:
                return "\n".join([x.strip() for x in str(doc).splitlines()])
            else:
                return self.nohelp % (arg,)
        except AttributeError:
            return self.nohelp % (arg,)
                    
    def do_help(self, opts, args):
        arg = " ".join(args)
        if arg:
            # XXX check arg syntax
            func = getattr(self, 'help_' + arg, None)
            if func is not None:
                func()
            else:
                print self.aligned_docstring(arg)
            parser = self.parser()
            optparse_func = getattr(self, 'opts_' + arg, lambda x: x)
            optparse_func(parser)
            parser.print_help()
        else:
            names = self.get_names()
            cmds_doc = []
            cmds_undoc = []
            help = {}
            for name in names:
                if name[:5] == 'help_':
                    help[name[5:]]=1
            names.sort()
            # There can be duplicates if routines overridden
            prevname = ''
            for name in names:
                if name[:3] == 'do_':
                    if name == prevname:
                        continue
                    prevname = name
                    cmd=name[3:]
                    if cmd in help:
                        cmds_doc.append(cmd)
                        del help[cmd]
                    elif getattr(self, name).__doc__:
                        cmds_doc.append(cmd)
                    else:
                        cmds_undoc.append(cmd)
            self.stdout.write("%s\n"%str(self.doc_leader))
            self.print_topics(self.doc_header,   cmds_doc,   15,80)
            self.print_topics(self.misc_header,  help.keys(),15,80)
            self.print_topics(self.undoc_header, cmds_undoc, 15,80)
        
    def simple_help(self, command):
        self.do_help((),(command,))


class YaybuCmd(OptionParsingCmd):
    
    prompt = "yaybu> "
    
    def __init__(self, ypath=(), verbose=2, logfile=None):
        """ Global options are provided on the command line, before the
        command """
        cmd.Cmd.__init__(self)
        self.ypath = ypath
        self.verbose = verbose
        self.logfile = logfile
        
    def preloop(self):
        print version()

    def opts_remote(self, parser):
        parser.add_option("-s", "--simulate", default=False, action="store_true")
        parser.add_option("-u", "--user", default="root", action="store", help="User to attempt to run as")
        parser.add_option("--resume", default=False, action="store_true", help="Resume from saved events if terminated abnormally")
        parser.add_option("--no-resume", default=False, action="store_true", help="Clobber saved event files if present and do not resume")
        parser.add_option("--env-passthrough", default=[], action="append", help="Preserve an environment variable in any processes Yaybu spawns")
 
    def do_remote(self, opts, args):
        """
        This command is invoked on remote systems by Yaybu and should not be used by humans
        """
        if os.path.exists("/etc/yaybu"):
            config = yay.load_uri("/etc/yaybu")
            opts.env_passthrough = config.get("env-passthrough", opts.env_passthrough)
        r = runner.Runner()
        try:
            ctx = None
            ctx = runcontext.RemoteRunContext("-", 
                                    resume=opts.resume,
                                    no_resume=opts.no_resume,
                                    ypath=self.ypath,
                                    simulate=opts.simulate,
                                    verbose=self.verbose,
                                    env_passthrough=opts.env_passthrough,
                                    )
            ctx.changelog.configure_audit_logging()
            rv = r.run(ctx)
        except error.Error as e:
            if ctx:
                ctx.changelog.write(str(e))
            return e.returncode

        if rv != 0:
            raise SystemExit(rv)
        return rv

    def opts_apply(self, parser):
        parser.add_option("-s", "--simulate", default=False, action="store_true")
        #parser.add_option("--host", default=None, action="store", help="A host to remotely run yaybu on")
        parser.add_option("-u", "--user", default="root", action="store", help="User to attempt to run as")
        parser.add_option("--resume", default=False, action="store_true", help="Resume from saved events if terminated abnormally")
        parser.add_option("--no-resume", default=False, action="store_true", help="Clobber saved event files if present and do not resume")
        parser.add_option("--env-passthrough", default=[], action="append", help="Preserve an environment variable in any processes Yaybu spawns")
        
    def do_apply(self, opts, args):
        """
        usage: apply [options] <filename>
        Applies the specified file to the current host
        """
        if os.path.exists("/etc/yaybu"):
            config = yay.load_uri("/etc/yaybu")
            opts.env_passthrough = config.get("env-passthrough", opts.env_passthrough)
        r = runner.Runner()
        ctx = runcontext.RunContext(args[0], 
                                    resume=opts.resume,
                                    no_resume=opts.no_resume,
                                    user=opts.user,
                                    ypath=self.ypath,
                                    simulate=opts.simulate,
                                    verbose=self.verbose,
                                    env_passthrough=opts.env_passthrough,
                                    )
        ctx.changelog.configure_audit_logging()
        rv = r.run(ctx)
        if rv != 0:
            raise SystemExit(rv)
        return rv
    
    def opts_push(self, parser):
        parser.add_option("-s", "--simulate", default=False, action="store_true")
        parser.add_option("--host", default=None, action="store", help="A host to remotely run yaybu on")
        parser.add_option("-u", "--user", default="root", action="store", help="User to attempt to run as")
        parser.add_option("--resume", default=False, action="store_true", help="Resume from saved events if terminated abnormally")
        parser.add_option("--no-resume", default=False, action="store_true", help="Clobber saved event files if present and do not resume")
        parser.add_option("--env-passthrough", default=[], action="append", help="Preserve an environment variable in any processes Yaybu spawns")
            
    def do_push(self, opts, args):
        """
        usage: remote [options] <hostname> <filename>
        Provision the specified hostname with the specified configuration, by
        executing Yaybu on the remote system, via ssh
        """
        if opts.host == "test://":
            opts.host = "localhost"
            RUNNER = remote.TestRemoteRunner
        else:
            RUNNER = remote.RemoteRunner

        ctx = runcontext.RunContext(args[0],
                                    resume=opts.resume,
                                    no_resume=opts.no_resume,
                                    user=opts.user,
                                    ypath=self.ypath,
                                    simulate=opts.simulate,
                                    verbose=self.verbose,
                                    env_passthrough=opts.env_passthrough,
                                    )

        r = RUNNER(ctx.host)
        rv = r.run(ctx)
        return rv

    def do_bootstrap(self, opts, args):
        """
        usage: bootstrap [options] <username>@<hostname>:<port>
        Prepare the specified target to run Yaybu
        """
        host = args[0]
        username = "ubuntu"
        port = 22

        if "@" in host:
            username, host = host.split("@", 1)

        if ":" in host:
            host, port = host.rsplit(":", 1)

        r = remote.RemoteRunner(host, username=username, port=port)
        try:
            r.install_yaybu()
        except error.Error as e:
            print str(e)
            return e.returncode

        return 0
 
    def do_expand(self, opts, args):
        """
        usage: expand [filename]
        Prints the expanded YAML for the specified file.
        """
        if len(args) != 1:
            self.simple_help("expand")
            return
        ctx = runcontext.RunContext(args[0], 
                                    ypath=self.ypath,
                                    verbose=self.verbose,
                                    )

        try:
            cfg = ctx.get_config().get()
        except yay.errors.LanguageError as e:
            print str(e)
            if self.verbose >= 2:
                print yay.errors.get_exception_context()
            return 1

        if self.verbose <= 2:
            cfg = dict(resources=cfg.get("resources", []))
        print yay.dump(cfg)

        return 0

    def do_status(self, opts, args):
        """
        usage: status <provider> [cluster]
        Describe the status of the cluster in the specified cloud.
        If no cluster is specified, all clusters are shown
        """
        
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
    
    def extract_roles(self, ctx, provider):
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
                self.get_key(ctx, provider, get_encrypted(v['key'])),
                get_encrypted(v['instance']['image']),
                get_encrypted(v['instance']['size']),
                get_encrypted(v.get('depends', ())),
                dns,
                get_encrypted(v.get('min', 0)),
                get_encrypted(v.get('max', None)))
            
    def get_cluster(self, ctx, provider, cluster_name, filename):
        """ Create a ScalableCloud object from the configuration provided.
        """
        
        clouds = ctx.get_config().mapping.get('clouds').resolve()
        p = clouds.get(provider, None)
        if p is None:
            raise KeyError("provider %r not found" % provider)
        roles = self.extract_roles(ctx, provider)
        cloud = AbstractCloud(
            get_encrypted(p['providers']['compute']), 
            get_encrypted(p['providers']['storage']), 
            get_encrypted(p['providers']['dns']),
            get_encrypted(p['args']), 
            get_encrypted(p['images']), 
            get_encrypted(p['sizes']), 
            )
        cluster = Cluster(cloud, cluster_name, roles)
        return cluster
    
    def delete_cloud(self, ctx, provider, cluster_name, filename):
        clouds = ctx.get_config().mapping.get('clouds').resolve()
        p = clouds.get(provider, None)
        if p is None:
            raise KeyError("provider %r not found" % provider)
        
    
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
        
    def decorate_config(self, ctx, provider, cluster, yargs=None, cloud=None):
        """ Update the configuration with the details for all running nodes """
        new_cfg = {'hosts': [],
                   'yaybu': {
                       'provider': provider,
                       'cluster': cluster,
                       'argv': {},
                       }
                   }
        if yargs is not None:
            for k, v in yargs.items():
                new_cfg['yaybu']['argv'][k] = v
        ctx.get_config().add(new_cfg)
        if cloud is not None:
            roles = ctx.get_config().mapping.get('roles').resolve()
            for role_name, role in cloud.roles.items():
                for node in role.nodes.values():
                    node_info = cloud.get_node_info(node)
                    struct = self.host_info(node_info, role_name, roles[role_name])
                    new_cfg['hosts'].append(struct)
        ctx.get_config().add(new_cfg)
        
    def analyze_args(self, ctx):
        """ Extract the arguments from the yaybu.argv key and return a parser """
        parser = YaybuArgParser()
        try:
            args = ctx.get_config().mapping.get('yaybu').get('options').resolve()
        except yay.errors.NoMatching:
            args = []
        for arg in args:
            if 'name' not in arg:
                raise KeyError("No name specified for an argument")
            yarg = YaybuArg(arg['name'], 
                            arg.get('type', 'string'),
                            arg.get('default', None),
                            arg.get('help', None)
                            )
            parser.add(yarg)
        return parser
        
    def opts_provision(self, parser):
        parser.add_option("-s", "--simulate", default=False, action="store_true")
        parser.add_option("-u", "--user", default="root", action="store", help="User to attempt to run as")
        parser.add_option("--resume", default=False, action="store_true", help="Resume from saved events if terminated abnormally")
        parser.add_option("--no-resume", default=False, action="store_true", help="Clobber saved event files if present and do not resume")
        parser.add_option("--env-passthrough", default=[], action="append", help="Preserve an environment variable in any processes Yaybu spawns")
        parser.add_option("-D", "--dump", default=False, action="store_true", help="Dump complete, *insecure* dumps of the configurations applied")
    
    def create_initial_context(self, provider, cluster_name, filename, args=None):
        """ Creates a context suitable for instantiating a cloud """
        ctx = runcontext.RunContext(filename, ypath=self.ypath, verbose=self.verbose)
        self.decorate_config(ctx, provider, cluster_name, args)
        return ctx
    
    def create_host_context(self, hostname, provider, cluster_name, filename, args, cloud):
        """ Creates the context used to provision an actual host """
        ctx = runcontext.RunContext(filename, ypath=self.ypath, verbose=self.verbose, resume=True)
        self.decorate_config(ctx, provider, cluster_name, args, cloud)
        ctx.set_host(hostname)
        ctx.get_config().load_uri("package://yaybu.recipe/host.yay")
        return ctx

    def create_runner(self, ctx, provider, hostname):
        """ Create a runner for the specified host, using the key found in
        the configuration """
        hosts = ctx.get_config().mapping.get("hosts").resolve()
        host = filter(lambda h: h['fqdn'] == hostname, hosts)[0]
        key_name = host['role']['key']
        key = self.get_key(ctx, provider, key_name)
        r = remote.RemoteRunner(hostname, key)
        return r
    
    def dump(self, ctx, filename):
        """ Dump the configuration in a raw form """
        cfg = ctx.get_config().get()
        open(filename, "w").write(yay.dump(cfg))
        
    def do_provision(self, opts, args):
        """
        usage: provision <provider> <cluster> <filename> <name=value>...
        Create a new cluster, or update the existing cluster, <cluster>
        in the cloud <provider>, using the configuration in <filename>
        if the configuration takes arguments these can be provided as 
        name=value name=value...
        """
        if len(args) < 3:
            self.simple_help("provision")
            return
        provider, cluster_name, filename = args[:3]
        ctx = self.create_initial_context(provider, cluster_name, filename)
        yarg_parser = self.analyze_args(ctx)
        yargs = yarg_parser.parse(args[3:])
        ctx = self.create_initial_context(provider, cluster_name, filename, yargs)
        cloud = self.get_cluster(ctx, provider, cluster_name, filename)
        cloud.provision_roles()
        logger.info("Provisioning completed, updating hosts")
        for hostname in cloud.get_all_hostnames():
            logger.info("Updating host %r" % hostname)
            host_ctx = self.create_host_context(hostname, provider, cluster_name, 
                                                filename, yargs, cloud)
            if opts.dump:
                self.dump(host_ctx, "%s.yay" % hostname)
            result = self.create_runner(host_ctx, provider, hostname).run(host_ctx)
            if result != 0:
                # stop processing further hosts
                return result
            
    def do_zoneupdate(self, opts, args):
        """ 
        usage: zoneupdate <provider> <cluster> <filename>
        Forces a DNS update for the specified configuration
        """
        if len(args) != 3:
            self.simple_help("zoneupdate")
            return
        provider, cluster_name, filename = args
        ctx = runcontext.RunContext(filename, ypath=self.ypath, verbose=self.verbose)
        cloud = self.get_cluster(ctx, provider, cluster_name, filename)
        for role, nodename in cloud.get_all_roles_and_nodenames():
            cloud.node_zone_update(role.name, nodename)
        
    def do_addnode(self, opts, args):
        """
        usage: addnode <provider> <cluster> <role>
        Add a new node of the specified role to the cluster
        """
        
    def do_rmnode(self, opts, args):
        """
        usage: rmnode <provider> <cluster> <nodeid>
        Delete the specified node
        """
        
    def do_ssh(self, opts, args):
        """ 
        usage: ssh <provider> <cluster> <name> 
        SSH to the node specified (with foo/bar/0 notation)
        """
        if len(args) != 3:
            self.do_help((),("ssh",))
            return
        provider, cluster_name, filename = args
        ctx = runcontext.RunContext(filename, ypath=self.ypath, verbose=self.verbose)
        cloud = self.get_cluster(ctx, provider, cluster_name, filename)
        # do some stuff
        
    def do_info(self, opts, args):
        """
        usage: info <provider> <cluster> <filename>
        Provide information on the specified cluster
        """
        if len(args) != 3:
            self.do_help((),("rmcluster",))
            return
        provider, cluster_name, filename = args
        ctx = runcontext.RunContext(filename, ypath=self.ypath, verbose=self.verbose)
        cloud = self.get_cluster(ctx, provider, cluster_name, filename)
        for role in cloud.roles_in_order():
            print "%s %s %s min %s max %s depends %s" % (
                role.name, role.image, role.size, role.min, role.max, role.depends)
            for node in role.nodes.values():
                n = cloud.cloud.nodes[node.their_name]
                print "    %s %s" % (node.their_name, n.extra['dns_name'])
        
    def do_rmcluster(self, opts, args):
        """
        usage: rmcluster <provider> <cluster> <filename>
        Delete the specified cluster completely
        """
        if len(args) != 3:
            self.do_help((),("rmcluster",))
            return
        provider, cluster_name, filename = args
        ctx = runcontext.RunContext(filename, ypath=self.ypath, verbose=self.verbose)
        logger.info("Deleting cluster")
        cloud = self.get_cluster(ctx, provider, cluster_name, filename)
        for role, name in cloud.get_all_roles_and_nodenames():
            logger.warning("Destroying %r on request" % (name,))
            cloud.destroy_node(role, name)
    
    def do_quit(self, opts=None, args=None):
        """ Exit yaybu """
        raise SystemExit
    
    def do_EOF(self, opts, args):
        """ Exit yaybu """
        print
        self.do_quit()

