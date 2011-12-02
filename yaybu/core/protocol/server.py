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
import shutil
from abc import ABCMeta, abstractmethod
from BaseHTTPServer import BaseHTTPRequestHandler
import StringIO

class RequestHandler(BaseHTTPRequestHandler):

    def __init__(self, rfile, wfile):
        self.rfile = rfile
        self.wfile = wfile

    def address_string(self):
        return 'stdio'

    def log_message(self, format, *args):
        # Uncomment to get HTTP request logs
        # super(RequestHandler, self).log_message(format, *args)
        return

    def handle_one_request(self):
        self.raw_requestline = self.rfile.readline()
        if not self.raw_requestline:
            self.close_connection = 1
            return False
        if not self.parse_request():
            return False

        path = self.path
        if "?" in path:
            path, self.getargs = path.split("?", 1)
        if "#" in path:
            path, self.bookmark = path.split("#", 1)
        self.path = filter(None, path.split("/"))

        return True

    def write_fileobj(self, fileobj):
        shutil.copyfileobj(fileobj, self.wfile)

    def send_error(self, code, message=None):
        """Send and log an error reply.

        We override the standard python code *soley* to keep the connection alive
        """

        try:
            short, long = self.responses[code]
        except KeyError:
            short, long = '???', '???'
        if message is None:
            message = short

        self.send_response(code, message)
        self.send_header("Content-Type", self.error_content_type)
        self.send_header('Connection', 'keepalive')
        self.end_headers()


class Server(object):

    def __init__(self, context, root, rfile=sys.stdin, wfile=sys.stdout):
        self.context = context
        self.root = root
        self.rfile = rfile
        self.wfile = wfile
        self.handlers = []

    def handle_request(self):
        # This will use BaseHTTPRequestHandler to parse HTTP headers off stdin,
        #   stdin is then ready to read any payload?
        r = RequestHandler(self.rfile, self.wfile)
        if not r.handle_one_request():
            return False

        node = self.root

        try:
            if r.path:
                segment, rest = r.path[0], r.path[1:]
                while segment:
                    node = node.get_child(segment)
                    if node.leaf:
                        break
                    if not rest:
                        break
                    segment, rest = rest[0], rest[1:]
 
            node.render(self.context, r, "/".join(rest))
        except Error, e:
            e.render(r, None)

        return True

    def serve_forever(self):
        while self.handle_request():
            pass


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
        if not hasattr(self, "render_" + request.command):
            raise MethodNotSupported(request.command)
        getattr(self, "render_" + request.command)(yaybu, request, postpath)


class StaticResource(HttpResource):

    leaf = True

    def __init__(self, content):
        super(StaticResource, self).__init__()
        self.content = content

    def render_GET(self, yaybu, request, postpath):
        request.send_response(200, "OK")
        request.send_header("Content-Type", "application/json")
        request.send_header("Content-Length", str(len(self.content)))
        request.send_header("Content", "keep-alive")
        request.end_headers()
        request.write_fileobj(StringIO.StringIO(self.content))


class AboutResource(HttpResource):

    leaf = True

    def get_version(self, thing):
        """ Returns the version of a python egg. Returns 0 if it can't be determined """
        import pkg_resources
        try:
            return pkg_resources.get_distribution(thing).version
        except pkg_resources.DistributionNotFound:
            return "0"

    def render_GET(self, yaybu, request, postpath):    
        request.send_response(200, "OK")
        request.send_header("Content-Type", "text/plain")
        request.send_header("Content-Length", "0")
        request.send_header("Content", "keep-alive")
        request.send_header("Yaybu", self.get_version("Yaybu"))
        request.send_header("yay", self.get_version("yay"))
        request.end_headers()
        request.write_fileobj(StringIO.StringIO(""))

