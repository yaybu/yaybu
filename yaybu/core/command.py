
""" Provides command-driven input to yaybu, using cmd.Cmd """

import os
import sys
import cmd
import optparse
import copy
import logging
import pprint
from functools import partial

import yay
import yay.errors
from yaybu.core import error, util
from yaybu.util import is_mac_bundle

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

            try:
                return func(opts, args)

            except error.ExecutionError, e:
                print str(e)
                return e.returncode

            except error.Error, e:
                print str(e)
                return e.returncode

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


class BaseYaybuCmd(OptionParsingCmd):

    prompt = "yaybu> "

    def __init__(self, config=None, ypath=(), verbose=2, logfile=None):
        """ Global options are provided on the command line, before the
        command """
        cmd.Cmd.__init__(self)
        self.config = config
        self.ypath = ypath
        self.verbose = verbose
        self.logfile = logfile

    @property
    def yaybufile(self):
        if self.config:
            return self.config

        directory = os.getcwd()
        while directory != "/":
            path = os.path.join(directory, "Yaybufile")
            if os.path.exists(path):
                return path
            directory = os.path.dirname(directory)

        # Ew. I might just refuse to support this.
        if os.path.exists("/Yaybufile"):
            return "/Yaybufile"

        raise error.MissingAsset("Could not find Yaybufile in '%s' or any of its parents" % os.getcwd())

    def preloop(self):
        print util.version()
        print ""

    def _get_graph(self, opts, args):
        from yaybu.core.config import Config
        graph = Config()
        graph.simulate = getattr(opts, "simulate", True)
        graph.resume = getattr(opts, "resume", False)
        graph.no_resume = getattr(opts, "no_resume", False)
        if not len(self.ypath):
            self.ypath = [os.getcwd()]
        graph.ypath = self.ypath
        graph.verbose = self.verbose

        graph.name = "example"
        graph.load_uri(os.path.realpath(self.yaybufile))
        if len(args) > 1:
            graph.set_arguments_from_argv(args[1:])

        return graph

    def _resolve_graph(self, graph, expect_changes=False):
        cfg = graph.resolve()

        if expect_changes and not graph.changelog.changed:
            raise error.NothingChanged("No changes were required")

        return 0, cfg

    def do_expand(self, opts, args):
        """
        usage: expand
        Prints the expanded YAML for the specified file.
        """
        graph = self._get_graph(opts, args)
        graph.readonly = True
        resolved = graph.resolve()
        print pprint.pprint(resolved)
        return 0

    def do_test(self, opts, args):
        """
        usage: test
        Test configuration is as valid as possible before deploying it
        """
        graph = self._get_graph(opts, args)
        graph.readonly = True
        graph.resolve()

        for actor in graph.actors:
            print type(actor), id(actor)
            actor.test()

        return 0

    def opts_up(self, parser):
        parser.add_option("-s", "--simulate", default=False, action="store_true")
        parser.add_option("--resume", default=False, action="store_true", help="Resume from saved events if terminated abnormally")
        parser.add_option("--no-resume", default=False, action="store_true", help="Clobber saved event files if present and do not resume")
        parser.add_option("--env-passthrough", default=[], action="append", help="Preserve an environment variable in any processes Yaybu spawns")

    def do_up(self, opts, args):
        """
        usage: up <name=value>...
        Create a new cluster, or update an existing cluster,
        in the cloud provider, using the configuration in Yaybufile
        if the configuration takes arguments these can be provided as
        name=value name=value...
        """
        graph = self._get_graph(opts, args)
        graph.readonly = True
        graph.resolve()

        for actor in graph.actors:
            actor.test()

        graph = self._get_graph(opts, args)
        graph.resolve()

        if not graph.changelog.changed:
            raise error.NothingChanged("No changes were required")

        return 0

    def do_ssh(self, opts, args):
        """
        usage: ssh <name>
        SSH to the node specified (with foo/bar/0 notation)
        """
        if len(args) < 1:
            self.do_help((),("ssh",))
            return

        graph = self._get_graph(opts, args)
        graph.readonly = True
        raise NotImplementedError("I don't know how to find compute nodes in the graph yet")

    def do_status(self, opts, args):
        """
        usage: status
        Provide information on the cluster
        """
        graph = self._get_graph(opts, args)
        graph.readonly = True
        raise NotImplementedError("I don't know how to find nodes in the graph yet")

    def do_destroy(self, opts, args):
        """
        usage: destroy <cluster> <filename>
        Delete the specified cluster completely
        """
        graph = self._get_graph(opts, args)

    def do_quit(self, opts=None, args=None):
        """ Exit yaybu """
        raise SystemExit

    def do_EOF(self, opts, args):
        """ Exit yaybu """
        print
        self.do_quit()


class BundledDarwinYaybuCmd(BaseYaybuCmd):

    def preloop(self):
        BaseYaybuCmd.preloop(self)
        if not self.is_on_path():
            print "Run 'link' in this window to be able to run 'yaybu' from an ordinary terminal."
            print ""

    def is_on_path(self):
        for path in os.environ.get("PATH", "").split(":"):
                bin = os.path.join(path, "yaybu")
                if os.path.exists(bin):
                    return True
        return False

    def do_link(self, opts, args):
        if self.is_on_path():
            print "Already on path!"
            return 1

        prefix = sys.argv[0]
        bundle = prefix[:prefix.find("Yaybu.app")+len("Yaybu.app")]

        f = os.path.join(bundle, "Contents", "Resources", "bin", "yaybu")
        t = "/usr/local/bin/yaybu"
        os.system("osascript -e 'do shell script \"test ! -d /usr/local/bin && mkdir -p /usr/local/bin; ln -s %s %s\" with administrator privileges'" % (f, t))


if is_mac_bundle():
    YaybuCmd = BundledDarwinYaybuCmd
else:
    YaybuCmd = BaseYaybuCmd

