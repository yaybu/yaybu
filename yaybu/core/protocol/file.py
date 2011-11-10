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

import os
from urlparse import urlparse, parse_qs

from yaybu.core.protocol.server import HttpResource
from yaybu.core import error

class FileResource(HttpResource):

    leaf = True

    def render_GET(self, yaybu, request, restpath):
        params = parse_qs(request.getargs)

        try:
            # Always read in binary mode. Opening files in text mode may cause
            # newline translations, making the actual size of the content
            # transmitted *less* than the content-length!
            f = yaybu.get_file(params["path"][0])
        except error.MissingAsset:
            request.send_error(404, "File not found")
            return None

        request.send_response(200, "OK")
        request.send_header("Content-Type", "application/octect-stream")
        request.send_header("Content-Length", str(f.len))
        #request.send_header("Last-Modified", self.date_time_string(fs.st_mtime))
        request.send_header("Content", "keep-alive")
        request.end_headers()

        request.write_fileobj(f)


class EncryptedResource(HttpResource):

    leaf = True

    def render_GET(self, yaybu, request, restpath):
        contents = yaybu.get_decrypted_file(restpath).read()

        request.send_response(200, "OK")
        request.send_header("Content-Type", "application/octect-stream")
        request.send_header("Content-Length", str(len(contents)))
        request.send_header("Content", "keep-alive")
        request.end_headers()

        request.wfile.write(contents)

