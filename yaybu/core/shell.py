# Copyright 2011 Isotoma Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import subprocess
import StringIO
import change
import error
import os, getpass, pwd, grp, select
import shlex
import pipes

from yay import String

from . import error

class Command(String):
    """ Horrible horrible cludge """
    pass


class ShellCommand(change.Change):

    """ Execute and log a change """

    def __init__(self, factory, command, shell, stdin, cwd=None, env=None, env_passthru=None, verbose=0, inert=False, user=None, group=None, simulate=False, umask=None):
        self.factory = factory
        self.command = command
        self.shell = shell
        self.stdin = stdin
        self.cwd = cwd
        self.env = env
        self.env_passthru = env_passthru
        self.verbose = verbose
        self.inert = inert
        self.simulate = simulate
        self._generated_env = {}

        self.user = None
        self.group = None
        self.homedir = None

        self.umask = umask

    def _tounicode(self, l):
        """ Ensure all elements of the list are unicode """
        def uni(x):
            if type(x) is type(u""):
                return x
            return unicode(x, "utf-8")
        return map(uni, l)

    def apply(self, renderer):
        ctx = self.factory.context
        vfs = ctx.vfs

        if isinstance(self.command, Command):
            logas = self.command.as_list(secret=True)
            command = self.command.as_list(secret=False)
        elif isinstance(self.command, String):
            logas = shlex.split(self.command.protected.encode("UTF-8"))
            command = shlex.split(self.command.unprotected.encode("UTF-8"))
        elif isinstance(self.command, list):
            logas = command = self.command[:]
        elif isinstance(self.command, basestring):
            logas = command = shlex.split(self.command.encode("UTF-8"))

        command = self._tounicode(command)
        logas = self._tounicode(logas)

        renderer.inert = self.inert
        renderer.command(logas)

        env = {
            #"HOME": "/home/" + self.user,
            #"LOGNAME": self.user,
            "PATH": "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
            "SHELL": "/bin/sh",
            }

        if self.env_passthru:
            for var in self.env_passthru:
                if var in os.environ:
                    env[var] = os.environ[var]

        if self.env:
            for key, item in self.env.iteritems():
                if isinstance(item, String):
                    env[key] = item.unprotected.encode("UTF-8")
                else:
                    env[key] = item

        self._generated_env = env

        if self.simulate and not self.inert:
            self.returncode = 0
            self.stdout = ""
            self.stderr = ""
            return

        command_exists = True
        if command[0].startswith("./"):
            if len(command[0]) <= 2:
                command_exists = False
            if not vfs.exists(os.path.join(self.cwd, command[0][2:])):
                command_exists = False

        elif command[0].startswith("/"):
            if not vfs.exists(command[0]):
                command_exists = False

        else:
            for path in env["PATH"].split(":"):
                if vfs.exists(os.path.join(path, command[0])):
                    break
            else:
                command_exists = False

        if not command_exists:
            if not self.simulate:
                raise error.BinaryMissing("Command '%s' not found" % command[0])
            renderer.stderr("Command '%s' not found; assuming this recipe will create it" % command[0])
            self.returncode = 0
            self.stdout = ""
            self.stderr = ""
            return

        self.returncode, self.stdout, self.stderr = self.factory._execute(command, renderer, stdin=self.stdin, env=env)


class Handle(object):

    def __init__(self, handle, callback=None):
        self.handle = handle
        self.callback = callback
        self._output = []

    def fileno(self):
        return self.handle.fileno()

    def read(self):
        data = os.read(self.fileno(), 1024)
        if data == "":
            self.handle.close()
            return False

        self._output.append(data)

        if self.callback:
            for l in data.splitlines():
                self.callback(l + "\r")

        return True

    def isready(self):
        return bool(self.handle)

    @property
    def output(self):
        out = ''.join(self._output)
        return out


class ShellTextRenderer(change.TextRenderer):

    """ Render a ShellCommand on a textual changelog. """

    renderer_for = ShellCommand
    inert = False

    def command(self, command):
        if not self.inert:
            self.logger.notice(u"# " + u" ".join(command))

    def output(self, returncode):
        if self.verbose >= 1 and returncode != 0 and not self.inert:
            self.logger.notice("returned %s", returncode)

    def stdout(self, data):
        if self.verbose >= 2 and not self.inert:
            self.logger.info(data)

    def stderr(self, data):
        if self.verbose >= 1:
            self.logger.info(data)

    def exception(self, exception):
        self.logger.notice("Exception: %r" % exception)


class Shell(object):

    """ This object wraps a shell in yet another shell. When the shell is
    switched into "simulate" mode it can just print what would be done. """

    def __init__(self, context, verbose=0, simulate=False, environment=None):
        self.simulate = context.simulate
        self.verbose = context.verbose
        self.context = context

        self.environment = ["SSH_AUTH_SOCK"]
        if environment:
            self.environment.extend(environment)

    def execute(self, command, stdin=None, shell=False, inert=False, cwd=None, env=None, user=None, group=None, umask=None, expected=0):
        cmd = ShellCommand(self, command, shell, stdin, cwd, env, self.environment, self.verbose, inert, user, group, self.simulate, umask)
        self.context.changelog.apply(cmd)
        if expected is not None and cmd.returncode != 0:
            raise error.SystemError(cmd.returncode, cmd.stdout, cmd.stderr)
        return (cmd.returncode, cmd.stdout, cmd.stderr)


class LocalShell(Shell):

    def communicate(self, p, stdout_fn=None, stderr_fn=None):
        if p.stdin:
            p.stdin.flush()
            p.stdin.close()

        stdout = Handle(p.stdout, stdout_fn)
        stderr = Handle(p.stderr, stderr_fn)

        # Initial readlist is any handle that is valid
        readlist = [h for h in (stdout, stderr) if h.isready()]

        while readlist:
            try:
                # Wait for data on stdout or stderr handles, but timeout after
                # one second so that we can poll (below) and check the process
                # hasn't disappeared.
                rlist, wlist, xlist = select.select(readlist, [], [], 1)
            except select.error, e:
                if e.args[0] == errno.EINTR:
                    continue
                raise

            # Some processes hang if we don't specifically poll for them going
            # away. We believe that under certain cases, child processes can
            # reuse their parent's file descriptors, and in that case, the
            # select loop will continue until the child process goes away, which
            # is undesirable when starting a daemon process.
            if not rlist and not wlist and not xlist:
                if p.poll() != None:
                    break

            # Read from all handles that select told us can be read from
            # If they return false then we are at the end of the stream
            # and stop reading from them
            for r in rlist:
                if not r.read():
                    readlist.remove(r)

        returncode = p.wait()

        return returncode, stdout.output, stderr.output

    def _execute(self, command, renderer):
        try:
            p = subprocess.Popen(command,
                                 shell=self.shell,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 cwd=self.cwd,
                                 env=None,
                                 preexec_fn=self.preexec,
                                 )
            returncode, stdout, stderr = self.communicate(p, renderer.stdout, renderer.stderr)
            renderer.output(p.returncode)
            return returncode, stdout, stderr
        except Exception, e:
            renderer.exception(e)
            raise


import paramiko as ssh

class RemoteShell(Shell):

    connection_attempts = 10
    missing_host_key_policy = ssh.AutoAddPolicy()
    key = None
    _client = None

    def connect(self):
        if self._client:
            return self._client

        client = ssh.SSHClient()
        client.set_missing_host_key_policy(self.missing_host_key_policy)
        for tries in range(self.connection_attempts):
            try:
                if self.key is not None:
                    client.connect(hostname=self.context.host,
                                   username=self.context.connect_user or "ubuntu",
                                   port=self.context.port or 22,
                                   pkey=self.key,
                                   look_for_keys=False)
                else:
                    client.connect(hostname=self.context.host,
                                   username=self.context.connect_user or "ubuntu",
                                   port=self.context.port or 22,
                                   look_for_keys=True)
                break

            except ssh.PasswordRequiredException:
                raise error.ConnectionError("Unable to authenticate with remote server")

            except (socket.error, EOFError):
                logger.warning("connection refused. retrying.")
                time.sleep(tries + 1)
        else:
            client.close()
            raise error.ConnectionError("Connection refused %d times, giving up." % self.connection_attempts)
        self._client = client
        return client

    def _refresh_intel(self):
        """ Thinking we grab env, users, groups, etc so we can do extra pre-validation... """
        pass

    def _execute(self, command, renderer, user="root", group=None, stdin=None, env=None):
        client = self.connect() # This should be done once per context object
        transport = client.get_transport()

        # No need to change user if we are already the right one
        if user == transport.get_username():
            user = None

        full_command = []
        if user or group:
            full_command.append('sudo')
        if user:
            full_command.extend(['-u', user])
        if group:
            full_command.extend(['-g', group])

        if isinstance(command, list):
            command = " ".join([pipes.quote(c) for c in command])
        
        if env:
            vars = []
            for k, v in env.items():
                vars.append("%s=%s" % (k, pipes.quote(v)))
            command = "export " + " ".join(vars) + "; " + command
            full_command.extend(["env", "-"])

        full_command.extend(["sh", "-c", command])

        # print ' '.join([pipes.quote(c) for c in full_command])

        channel = transport.open_session()
        channel.exec_command(' '.join([pipes.quote(c) for c in full_command]))
        
        if stdin:
            channel.send(stdin)
            channel.shutdown_write()

        stdout = ""
        while not channel.exit_status_ready():
            rlist, wlist, xlist = select.select([channel], [], [])
            if not rlist:
                continue
            data = channel.recv(1024)
            stdout += data
        while channel.recv_ready():
            data = channel.recv(1024)
            stdout += data
        returncode = channel.recv_exit_status()
        return returncode, stdout, ''

