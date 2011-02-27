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

import sys
from httplib import HTTPResponse as BaseHTTPResponse
from httplib import HTTPConnection as BaseHTTPConnection

class FileSocket(object):
    """ I adapt a pair of file objects to look like a socket """

    def __init__(self, rfile, wfile):
        self.rfile = rfile
        self.wfile = wfile

    def sendall(self, data):
        self.wfile.write(data)
        self.wfile.flush()

    def makefile(self, mode, flags):
        if mode.startswith("r"):
            return self.rfile
        raise NotImplementedError

    def close(self):
        pass


class HTTPResponse(BaseHTTPResponse):

    def close(self):
        pass


class HTTPConnection(BaseHTTPConnection):

    response_class = HTTPResponse

    def __init__(self, rfile=sys.stdin, wfile=sys.stdout):
        self.rfile = rfile
        self.wfile = wfile

        BaseHTTPConnection.__init__(self, "stdio")

    def connect(self):
        self.sock = FileSocket(self.rfile, self.wfile)

