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

import os, logging, json

from yaybu.core.protocol.server import HttpResource


class ChangeLogResource(HttpResource):

    leaf = True

    def render_POST(self, context, request, restpath):
        body = json.loads(request.rfile.read(int(request.headers["content-length"])))

        # Python logging seems to screw up if this isnt a tuple
        body['args'] = tuple(body.get('args', []))

        logrecord = logging.makeLogRecord(body)
        context.changelog.handle(logrecord)

        request.send_response(200, "OK")
        request.send_header("Content-Type", "application/octect-stream")
        request.send_header("Content-Length", "0")
        request.send_header("Content", "keep-alive")
        request.end_headers()

