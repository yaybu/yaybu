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

import pipes
import select
import socket
import time
import paramiko
from paramiko.ssh_exception import SSHException
from paramiko.rsakey import RSAKey
from paramiko.dsskey import DSSKey
import StringIO

from yaybu import error
from . import remote, base


class SSHTransport(base.Transport, remote.RemoteTransport):

    connection_attempts = 20
    missing_host_key_policy = paramiko.AutoAddPolicy()
    _client = None

    def get_private_key(self, data):
        for KeyClass in (RSAKey, DSSKey):
            try:
                fp = StringIO.StringIO(data)
                return KeyClass.from_private_key(fp)
            except SSHException as e:
                pass
        raise RuntimeError("Invalid private_key")

    def connect(self):
        if self._client:
            return self._client

        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(self.missing_host_key_policy)
        for tries in range(self.connection_attempts):
            try:
                if self.context.password:
                    client.connect(hostname=self.context.host,
                                   username=self.context.user,
                                   port = self.context.port,
                                   password = self.context.password,
                                   look_for_keys = False)

                elif self.context.private_key:
                    private_key = self.context.root.openers.open(self.context.private_key).read()

                    client.connect(hostname=self.context.host,
                                   username=self.context.user,
                                   port=self.context.port,
                                   pkey=self.get_private_key(private_key),
                                   look_for_keys=False)
                else:
                    client.connect(hostname=self.context.host,
                                   username=self.context.user,
                                   port=self.context.port,
                                   look_for_keys=True)
                break

            except paramiko.PasswordRequiredException:
                raise error.ConnectionError("Unable to authenticate with remote server")

            except (socket.error, EOFError):
                # logger.warning("connection refused. retrying.")
                time.sleep(tries + 1)
        else:
            client.close()
            raise error.ConnectionError("Connection refused %d times, giving up." % self.connection_attempts)
        self._client = client
        return client

    def whoami(self):
        return self.connect().get_transport().get_username()

    def _execute(self, command, stdin, stdout, stderr):
        client = self.connect() # This should be done once per context object
        transport = client.get_transport()

        channel = transport.open_session()

        channel.exec_command(' '.join([pipes.quote(c) for c in command]))

        if stdin:
            channel.sendall(stdin)
            channel.shutdown_write()

        def recvr(ready, recv, cb, buffer):
            while ready():
                data = recv(1024)
                if data:
                    if cb:
                        cb(data)
                    buffer.append(data)

        stdout_buffer = []
        stderr_buffer = []
        while not channel.exit_status_ready():
            rlist, wlist, xlist = select.select([channel], [], [], 1)
            if not rlist:
                continue

            recvr(channel.recv_ready, channel.recv, stdout, stdout_buffer)
            recvr(channel.recv_stderr_ready, channel.recv_stderr, stderr, stderr_buffer)

        while not channel.eof_received:
            recvr(channel.recv_ready, channel.recv, stdout, stdout_buffer)
            recvr(channel.recv_stderr_ready, channel.recv_stderr, stderr, stderr_buffer)

        recvr(channel.recv_ready, channel.recv, stdout, stdout_buffer)
        recvr(channel.recv_stderr_ready, channel.recv_stderr, stderr, stderr_buffer)

        returncode = channel.recv_exit_status()

        channel.close()

        return returncode, ''.join(stdout_buffer), ''.join(stderr_buffer)

