
import socket
import ssh
from StringIO import StringIO

import time
import logging

# we need to do better than this
socket.setdefaulttimeout(10)

logger = logging.getLogger(__name__)

class TransientError(Exception):
    pass

class NodeSSH(object):
    
    def __init__(self, original):
        self.original = original
        
    # TODO: these time.sleeps should instead be going back on the queue
    def get_transport(self, username=None, keypair=None):
        try:
            t = ssh.Transport((self.original.hostname, self.original.ssh_port))
            t.start_client()
            connected = True
        except ssh.SSHException, e:
            logger.warning("Error while establishing transport: %s. retrying" % e)
            raise TransientError(e)
        except EOFError, e:
            logger.warning("EOFError while starting client. retrying.")
            raise TransientError(e)
        except socket.error, e:
            logger.warning("socket error: %s. retrying" % e)
            raise TransientError(e)
                
        if keypair is None:
            keypair = self.original.keypair
        if username is None:
            username = self.original.username
        key = ssh.RSAKey.from_private_key(StringIO(keypair.private))
        t.auth_publickey(username, key)
        return t
    
    def get_sftp(self, **kwargs):
        return ssh.SFTPClient.from_transport(self.get_transport(**kwargs))
    
    def get_ssh(self):
        client = ssh.SSHClient()
        client.set_missing_host_key_policy(ssh.AutoAddPolicy())
        key = ssh.RSAKey.from_private_key(StringIO(self.original.keypair.private))
        client.connect(hostname=self.original.hostname,
                       username=self.original.username,
                       pkey=key,
                       look_for_keys=False,
                       )
        return client