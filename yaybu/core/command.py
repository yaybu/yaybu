
""" Provides command-driven input to yaybu, using cmd.Cmd """

import os
import cmd
import optparse
import copy
import logging
from functools import partial

import yay
import yay.errors
from yaybu.core import runner, runcontext, error, util

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
        print util.version()

    def opts_apply(self, parser):
        parser.add_option("-s", "--simulate", default=False, action="store_true")
        #parser.add_option("--host", default=None, action="store", help="A host to remotely run yaybu on")
        parser.add_option("-u", "--user", default="root", action="store", help="User to attempt to run as")
        parser.add_option("--resume", default=False, action="store_true", help="Resume from saved events if terminated abnormally")
        parser.add_option("--no-resume", default=False, action="store_true", help="Clobber saved event files if present and do not resume")
        parser.add_option("--env-passthrough", default=[], action="append", help="Preserve an environment variable in any processes Yaybu spawns")

    def do_apply(self, opts, args, context=runcontext.RunContext):
        """
        usage: apply [options] <filename>
        Applies the specified file to the current host
        """
        if len(args) < 1:
            self.simple_help("apply")
            return
        if os.path.exists("/etc/yaybu"):
            config = yay.load_uri("/etc/yaybu")
            opts.env_passthrough = config.get("env-passthrough", opts.env_passthrough)
        r = runner.Runner()
        ctx = context(args[0],
                                    resume=opts.resume,
                                    no_resume=opts.no_resume,
                                    user=opts.user,
                                    ypath=self.ypath,
                                    simulate=opts.simulate,
                                    verbose=self.verbose,
                                    env_passthrough=opts.env_passthrough,
                                    )
        ctx.changelog.configure_audit_logging()
        if len(args) > 1:
            ctx.get_config().set_arguments_from_argv(args[1:])
        rv = r.run(ctx)
        #if rv != 0:
        #    raise SystemExit(rv)
        return rv

    def opts_push(self, parser):
        parser.add_option("-s", "--simulate", default=False, action="store_true")
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
        if len(args) < 2:
            self.simple_help("push")
            return

        hostname = args[0]
        ctx = runcontext.RunContext(args[1],
                                    resume=opts.resume,
                                    no_resume=opts.no_resume,
                                    user=opts.user,
                                    ypath=self.ypath,
                                    simulate=opts.simulate,
                                    verbose=self.verbose,
                                    env_passthrough=opts.env_passthrough,
                                    )

        if len(args) > 1:
            ctx.get_config().set_arguments_from_argv(args[2:])

        r = runner(hostname)
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
        usage: status [cluster]
        Describe the status of the cluster in the specified cloud.
        If no cluster is specified, all clusters are shown
        """

    def opts_provision(self, parser):
        parser.add_option("-s", "--simulate", default=False, action="store_true")
        parser.add_option("-u", "--user", default="root", action="store", help="User to attempt to run as")
        parser.add_option("--resume", default=False, action="store_true", help="Resume from saved events if terminated abnormally")
        parser.add_option("--no-resume", default=False, action="store_true", help="Clobber saved event files if present and do not resume")
        parser.add_option("--env-passthrough", default=[], action="append", help="Preserve an environment variable in any processes Yaybu spawns")
        parser.add_option("-D", "--dump", default=False, action="store_true", help="Dump complete, *insecure* dumps of the configurations applied")

    def do_provision(self, opts, args):
        """
        usage: provision <cluster> <filename> <name=value>...
        Create a new cluster, or update the existing cluster, <cluster>
        in the cloud provider, using the configuration in <filename>
        if the configuration takes arguments these can be provided as
        name=value name=value...
        """
        if len(args) < 2:
            self.simple_help("provision")
            return

        from yaybu.core.config import Config

        graph = Config()
        graph.simulate = opts.simulate
        graph.name = args[0]
        graph.load_uri(args[1])

        try:
            cfg = graph.resolve()
        except yay.errors.LanguageError as e:
            print str(e)
            if self.verbose >= 2:
                print yay.errors.get_exception_context()
            return 1

        return 0

    def do_ssh(self, opts, args):
        """
        usage: ssh <cluster> <name>
        SSH to the node specified (with foo/bar/0 notation)
        """
        if len(args) != 2:
            self.do_help((),("ssh",))
            return
        cluster_name, filename = args
        cluster = self.get_cluster(cluster_name, filename)
        # do some stuff
        raise NotImplementedError

    def do_info(self, opts, args):
        """
        usage: info <cluster> <filename>
        Provide information on the specified cluster
        """
        if len(args) != 2:
            self.do_help((),("rmcluster",))
            return
        cluster_name, filename = args
        cluster = Cluster(cluster_name, filename)
        print "Not implemented yet"

    def do_destroy(self, opts, args):
        """
        usage: destroy <cluster> <filename>
        Delete the specified cluster completely
        """
        if len(args) != 2:
            self.do_help((),("rmcluster",))
            return
        cluster_name, filename = args
        logger.info("Deleting cluster")
        cluster = Cluster(cluster_name, filename)
        cluster.destroy()

    def do_quit(self, opts=None, args=None):
        """ Exit yaybu """
        raise SystemExit

    def do_EOF(self, opts, args):
        """ Exit yaybu """
        print
        self.do_quit()

