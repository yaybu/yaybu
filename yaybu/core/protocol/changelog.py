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

from yaybu.core.protocol.server import HttpResource


class ChangeLogResource(HttpResource):

    leaf = True

    def do_write(self, ctx, body):
        ctx.changelog.write(body)

    def do_simlog_notice(self, ctx, body):
        ctx.changelog.simlog_notice(body)

    def do_simlog_info(self, ctx, body):
        ctx.changelog.simlog_info(body)

    def render_POST(self, context, request, restpath):
        body = request.rfile.read(int(request.headers["content-length"]))

        if not hasattr(self, "do_" + restpath):
            request.send_response(404, "Resource not found")
            return

        method = getattr(self, "do_" + restpath)
        method(context, body)

        request.send_response(200, "OK")
        request.send_header("Content-Type", "application/octect-stream")
        request.send_header("Content-Length", "0")
        request.send_header("Content", "keep-alive")
        request.end_headers()

