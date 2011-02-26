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

import subprocess

from yaybu.core.protocol.server import Server, HttpResource
from yaybu.core.protocol.file import FileResource

class RemoteRunner(object):

    def run(self, opt, args):
        p = subprocess.Popen(["ssh", "-A", opt.host, "yaybu", "--remote"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)

        root = HttpResource()
        root.put_child("files", FileResource())
        #root.put_child("changelog", Changelog())

        Server(root, p.stdout, p.stdin).serve_forever()

