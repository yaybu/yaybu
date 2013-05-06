# Copyright 2011-2013 Isotoma Limited
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

import os
import pipes
import select

import paramiko as ssh

from yay import String

from . import error


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
                # logger.warning("connection refused. retrying.")
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
