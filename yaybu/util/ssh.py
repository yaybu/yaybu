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

import getpass
import socket
import StringIO

import paramiko


def get_ssh_transport_for_node(node):
    hostname = node.fqdn.as_string()
    port = node.port.as_int(default=22)

    username = node.user.as_string(default=getpass.getuser())
    password = node.password.as_string(default=None)
    private_key = node.private_key.as_string(default=None)

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((hostname, port))

    t = paramiko.Transport(sock)
    t.start_client()

    if password and not t.is_authenticated():
        t.auth_password(username, password)

    if private_key and not t.is_authenticated():
        data = node.root.openers.open(private_key).read()

        for Key in (paramiko.RSAKey, paramiko.DSSKey):
            try:
                fp = StringIO.StringIO(data)
                key = Key.from_private_key(fp)
                t.auth_publickey(username, key)
            except paramiko.SSHException:
                pass

    if not t.is_authenticated():
        agent = paramiko.Agent()
        for key in agent.get_keys():
            try:
                t.auth_publickey(username, key)
            except paramiko.SSHException:
                pass

    if not t.is_authenticated():
        raise paramiko.SSHException("Could not auth")

    return t
