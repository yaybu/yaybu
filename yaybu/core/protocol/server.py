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
from abc import ABCMeta, abstractmethod
from BaseHTTPServer import BaseHTTPRequestHandler

class RequestHandler(BaseHTTPRequestHandler):

    def __init__(self, rfile, wfile):
        self.rfile = rfile
        self.wfile = wfile

    def address_string(self):
        return 'stdio'

    def handle_one_request(self):
        self.raw_requestline = self.rfile.readline()
        if not self.raw_requestline:
            self.close_connection = 1
            return False
        return self.parse_request()

    def write_fileobj(self, fileobj):
        shutil.copyfileobj(fileobj, self.wfile)


class Server(object):

    def __init__(self, root, rfile=sys.stdin, wfile=sys.stdout):
        self.root = root
        self.rfile = rfile
        self.wfile = wfile
        self.handlers = []

    def handle_request(self):
        # This will use BaseHTTPRequestHandler to parse HTTP headers off stdin,
        #   stdin is then ready to read any payload?
        r = RequestHandler(self.rfile, self.wfile)
        r.handle_one_request()

        segment, rest = r.path.split("/", 1)
        node = self.root

        while segment:
            if node.leaf:
                break
            node = node.getChild(segment)
            segment, rest = rest.split("/", 1)

        node.render(self.yaybu, r, rest)

    def serve_forever(self):
        while True:
            self.handle_request()


class Error(Exception):

    def render(self, request, post):
        request.send_error(self.error_code, self.error_string)


class NotFound(Error):

    error_code = 404
    error_string = "Resource not found"

class MethodNotSupported(Error):

    error_code = 501
    error_string = "Method not supported"


class HttpResource(object):

    leaf = False

    def __init__(self):
        self.children = {}

    def put_child(self, key, child):
        self.children[key] = child

    def get_child(self, key):
        if key in self.children:
            return self.children[key]
        raise NotFound(key)

    def render(self, yaybu, request, postpath):
        if not hasattr(self, "render_" + request.method):
            raise MethodNotSupported(request.method)
        getattr(self, "render_" + request.method)(yaybu, request, postpath)

