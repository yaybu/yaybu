
""" Provides command-driven input to yaybu, using cmd.Cmd """

import os
import cmd
import readline
import optparse

import yay
from yaybu.core import runner, remote, runcontext

class OptionParsingCmd(cmd.Cmd):

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
            parser = optparse.OptionParser()
            optparse_func = getattr(self, 'opts_' + cmd, lambda x: x)
            optparse_func(parser)
            opts, args = parser.parse_args(arg.split())
            return func(opts, args)

class YaybuCmd(OptionParsingCmd):
    
    prompt = "yaybu> "
    
    def __init__(self, ypath=(), verbose=2):
        """ Global options are provided on the command line, before the
        command """
        cmd.Cmd.__init__(self)
        self.ypath = ypath
        self.verbose = verbose
        
    def opts_provision(self, parser):
        parser.add_option("-s", "--simulate", default=False, action="store_true")
        parser.add_option("--host", default=None, action="store", help="A host to remotely run yaybu on")
        parser.add_option("-u", "--user", default="root", action="store", help="User to attempt to run as")
        #parser.add_option("--remote", default=False, action="store_true", help="Run yaybu.protocol client on stdio")
        #parser.add_option("--expand-only", default=False, action="store_true", help="Set to parse config, expand it and exit")
        parser.add_option("--resume", default=False, action="store_true", help="Resume from saved events if terminated abnormally")
        parser.add_option("--no-resume", default=False, action="store_true", help="Clobber saved event files if present and do not resume")
        parser.add_option("--env-passthrough", default=[], action="append", help="Preserve an environment variable in any processes Yaybu spawns")
    
    def do_provision(self, opts, args):
        # Probably not the best place to put this stuff...
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
    
    def help_provision(self):
        pass
    
    def opts_remote(self, opts, args):
        parser.add_option("-s", "--simulate", default=False, action="store_true")
        parser.add_option("--host", default=None, action="store", help="A host to remotely run yaybu on")
        parser.add_option("-u", "--user", default="root", action="store", help="User to attempt to run as")
        #parser.add_option("--remote", default=False, action="store_true", help="Run yaybu.protocol client on stdio")
        #parser.add_option("--expand-only", default=False, action="store_true", help="Set to parse config, expand it and exit")
        parser.add_option("--resume", default=False, action="store_true", help="Resume from saved events if terminated abnormally")
        parser.add_option("--no-resume", default=False, action="store_true", help="Clobber saved event files if present and do not resume")
        parser.add_option("--env-passthrough", default=[], action="append", help="Preserve an environment variable in any processes Yaybu spawns")
        
    
    def do_remote(self, opts, args):
        r = remote.RemoteRunner()
        r.load_system_host_keys()
        r.set_missing_host_key_policy("ask")
        ctx = runcontext.RemoteRunContext(args[0], opts)
        rv = r.run(ctx)
        return rv
        
    
    def do_expand(self, opts, args):
        """ Expand the yay file provided in the args """
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
        
    def help_expand(self):
        print """usage: expand [filename]
        
        Prints the expanded YAML for the specified file.
        """
    
    def do_status(self, opts, args):
        pass
    
    def do_help(self, opts, args):
        print ("Commands available:\n"
               "    provision\n"
               "    remote\n"
               "    expand\n")
        
    def do_quit(self, opts=None, args=None):
        raise SystemExit
    
    def do_EOF(self, opts, args):
        print
        self.do_quit()
        
        

