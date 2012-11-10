# Copyright 2012 Isotoma Limited
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
    
    
    
    
