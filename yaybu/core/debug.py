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

import pdb, socket, sys


class Rdb(pdb.Pdb):

    def __init__(self, port=4444):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self.socket.bind(("127.0.0.1", port))
        self.socket.listen(1)

        client, address = self.socket.accept()
        handle = client.makefile('rw')
        pdb.Pdb.__init__(self, completekey='tab', stdin=handle, stdout=handle)

    def do_continue(self, arg):
        self.socket.shutdown(socket.SHUT_RDWR)
        self.socket.close()
        self.socket = None
        self.set_continue()
        return 1

    def __enter__(self):
        return self

    def __exit__(self, *args):
        if self.socket:
            self.socket.shutdown(socket.SHUT_RDWR)
            self.socket.close()
        return False

def set_trace():
    Rdb().set_trace(sys._getframe().f_back)

def post_mortem(exc_traceback=None):
    if exc_traceback is None:
       exc_type, exc_value, exc_traceback = sys.exc_info()

    with Rdb() as p:
        p.reset()
        p.interaction(None, exc_traceback)

def pm():
    post_mortem(sys.last_traceback)

