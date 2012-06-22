
""" Provides command-driven input to yaybu, using cmd.Cmd """

import os
import cmd
import optparse
import copy
import logging
from functools import partial

import yay
from yaybu.core import runner, remote, runcontext
from yaybu.core.util import version, get_encrypted
from yaybu.core.cloud.cluster import Cluster, Role
from paramiko.ssh_exception import SSHException
from yaybu.core.cloud.cluster import Cluster

from paramiko.rsakey import RSAKey
from paramiko.dsskey import DSSKey

logger = logging.getLogger("yaybu.core.command")

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
        

class YaybuCmd(OptionParsingCmd):
    
    prompt = "yaybu> "
    
    def __init__(self, ypath=(), verbose=2):
        """ Global options are provided on the command line, before the
        command """
        cmd.Cmd.__init__(self)
        self.ypath = ypath
        self.verbose = verbose
        
    def preloop(self):
        print version()
        
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
        rv = r.run(ctx)
        if rv != 0:
            raise SystemExit(rv)
        return rv
    
    def opts_remote(self, opts, args):
        parser.add_option("-s", "--simulate", default=False, action="store_true")
        parser.add_option("--host", default=None, action="store", help="A host to remotely run yaybu on")
        parser.add_option("-u", "--user", default="root", action="store", help="User to attempt to run as")
        parser.add_option("--resume", default=False, action="store_true", help="Resume from saved events if terminated abnormally")
        parser.add_option("--no-resume", default=False, action="store_true", help="Clobber saved event files if present and do not resume")
        parser.add_option("--env-passthrough", default=[], action="append", help="Preserve an environment variable in any processes Yaybu spawns")
            
    def do_remote(self, opts, args):
        """
        usage: remote [options] <hostname> <filename>
        Provision the specified hostname with the specified configuration, by
        executing Yaybu on the remote system, via ssh
        """
        ctx = runcontext.RunContext(args[0], opts)
        r = remote.RemoteRunner(ctx.host)
        rv = r.run(ctx)
        return rv
    
    def do_expand(self, opts, args):
        """
        usage: expand [filename]
        Prints the expanded YAML for the specified file.
        """
        if len(args) != 1:
            self.help_expand()
            return
        ctx = runcontext.RunContext(args[0], 
                                    ypath=self.ypath,
                                    verbose=self.verbose,
                                    )
        cfg = ctx.get_config().get()

        if self.verbose <= 2:
            cfg = dict(resources=cfg.get("resources", []))
        print yay.dump(cfg)
        
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
            yield Role(
                k,
                get_encrypted(v['key']),
                self.get_key(ctx, provider, get_encrypted(v['key'])),
                get_encrypted(v['instance']['image']),
                get_encrypted(v['instance']['size']),
                get_encrypted(v.get('min', 0)),
                get_encrypted(v.get('max', None)))
            
    def create_cloud(self, ctx, provider, cluster_name, filename):
        """ Create a ScalableCloud object from the configuration provided.
        """
        
        clouds = ctx.get_config().mapping.get('clouds').resolve()
        p = clouds.get(provider, None)
        if p is None:
            raise KeyError("provider %r not found" % provider)
        roles = self.extract_roles(ctx, provider)
        cloud = Cluster(cluster_name, 
                        get_encrypted(p['providers']['compute']), 
                        get_encrypted(p['providers']['storage']), 
                        get_encrypted(p['args']), 
                        get_encrypted(p['images']), 
                        get_encrypted(p['sizes']), 
                        roles)
        return cloud
        
    def decorate_config(self, ctx, cloud):
        """ Update the configuration with the details for all running nodes """
        roles = ctx.get_config().mapping.get('roles').resolve()
        new_cfg = {'hosts': {}}
        for role_name, role in cloud.roles.items():
            for node in role.nodes.values():
                info = cloud.get_node_info(node)
                hostname = info['fqdn']
                new_cfg['hosts'][hostname] = copy.copy(info)
                new_cfg['hosts'][hostname]['role'] = {}
                new_cfg['hosts'][hostname]['role']['name'] = role_name
                for k, v in roles[role_name].items():
                    new_cfg['hosts'][hostname]['role'][k] = copy.copy(v)
        ctx.get_config().add(new_cfg) 
        
    def opts_provision(self, parser):
        parser.add_option("-s", "--simulate", default=False, action="store_true")
        parser.add_option("-u", "--user", default="root", action="store", help="User to attempt to run as")
        parser.add_option("--resume", default=False, action="store_true", help="Resume from saved events if terminated abnormally")
        parser.add_option("--no-resume", default=False, action="store_true", help="Clobber saved event files if present and do not resume")
        parser.add_option("--env-passthrough", default=[], action="append", help="Preserve an environment variable in any processes Yaybu spawns")
    
    def do_provision(self, opts, args):
        """
        usage: provision <provider> <cluster> <filename>
        Create a new cluster, or update the existing cluster, <cluster>
        in the cloud <provider>, using the configuration in <filename>
        """
        if len(args) != 3:
            self.help_provision()
            return
        provider, cluster_name, filename = args
        ctx = runcontext.RunContext(filename, ypath=self.ypath, verbose=self.verbose)
        cloud = self.create_cloud(ctx, provider, cluster_name, filename)
        cloud.provision_roles()
        for hostname in cloud.get_all_hostnames():
            # create a new context to decorate to isolate changes between nodes
            ctx = runcontext.RunContext(filename, ypath=self.ypath, verbose=self.verbose)
            self.decorate_config(ctx, cloud)
            host = ctx.get_config().mapping.get("hosts").resolve()[hostname]
            key_name = host['role']['key']
            key = self.get_key(ctx, provider, key_name)
            logger.info("Applying configuration to %r" % hostname)
            r = remote.RemoteRunner(hostname, key)
            ctx.set_host(hostname)
            ctx.get_config().load_uri("package://yaybu.recipe/host.yay")
            rv = r.run(ctx)
            if rv != 0:
                return rv
        
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
    
    def do_quit(self, opts=None, args=None):
        """ Exit yaybu """
        raise SystemExit
    
    def do_EOF(self, opts, args):
        """ Exit yaybu """
        print
        self.do_quit()
