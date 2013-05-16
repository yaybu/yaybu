
""" Provides command-driven input to yaybu, using cmd.Cmd """

import os
import cmd
import optparse
import copy
import logging
from functools import partial

import yay
import yay.errors
from yaybu.core import error, util

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

    def do_expand(self, opts, args):
        """
        usage: expand [filename]
        Prints the expanded YAML for the specified file.
        """
        if len(args) != 1:
            self.simple_help("expand")
            return
        return 1

    def do_status(self, opts, args):
        """
        usage: status [cluster]
        Describe the status of the cluster in the specified cloud.
        If no cluster is specified, all clusters are shown
        """

    def opts_up(self, parser):
        parser.add_option("-s", "--simulate", default=False, action="store_true")
        parser.add_option("-u", "--user", default="root", action="store", help="User to attempt to run as")
        parser.add_option("--resume", default=False, action="store_true", help="Resume from saved events if terminated abnormally")
        parser.add_option("--no-resume", default=False, action="store_true", help="Clobber saved event files if present and do not resume")
        parser.add_option("--env-passthrough", default=[], action="append", help="Preserve an environment variable in any processes Yaybu spawns")
        parser.add_option("-C", "--config", default="Yaybufile", action="store", help="Name of configuration to load")

    def do_up(self, opts, args):
        """
        usage: up <name=value>...
        Create a new cluster, or update an existing cluster,
        in the cloud provider, using the configuration in Yaybufile
        if the configuration takes arguments these can be provided as
        name=value name=value...
        """
        if os.path.exists("/etc/yaybu"):
            config = yay.load_uri("/etc/yaybu")
            opts.env_passthrough = config.get("env-passthrough", opts.env_passthrough)

        from yaybu.core.config import Config
        graph = Config()
        graph.simulate = opts.simulate
        graph.resume = opts.resume
        graph.no_resume = opts.no_resume
        graph.user = opts.user
        if not len(self.ypath):
            self.ypath.append(os.getcwd())
        graph.ypath = self.ypath
        graph.verbose = self.verbose
        graph.env_passthrough = opts.env_passthrough

        graph.name = "example"
        graph.load_uri(os.path.realpath(opts.config))
        if len(args) > 1:
            graph.set_arguments_from_argv(args[1:])

        try:
            cfg = graph.resolve()

        except yay.errors.LanguageError as e:
            print str(e)
            if self.verbose >= 2:
                print yay.errors.get_exception_context()
            return error.ParseError.returncode

        except error.ExecutionError, e:
            # this will have been reported by the context manager, so we wish to terminate
            # but not to raise it further. Other exceptions should be fully reported with
            # tracebacks etc automatically
            # graph.changelog.error("Terminated due to execution error in processing")
            print str(e)
            return e.returncode

        except error.Error, e:
            # If its not an Execution error then it won't have been logged by the
            # Resource.apply() machinery - make sure we log it here.
            print str(e)
            # graph.changelog.write(str(e))
            # graph.changelog.error("Terminated due to error in processing")
            return e.returncode

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

