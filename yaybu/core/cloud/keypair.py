import os
import base64
import subprocess
import tempfile
import os
from Crypto.PublicKey import RSA
from twisted.python import randbytes
from twisted.conch.ssh import keys

def generate_keypair(bits=2048):
    from Crypto.PublicKey import RSA
    # TODO: see if twisted.python.randbytes.secureRandom is better
    key = RSA.generate(bits, os.urandom)
    key_obj = keys.Key(key)
    private = key_obj.toString('openssh')
    public = key_obj.public().toString('openssh')
    return private, public 
    
    
    
    