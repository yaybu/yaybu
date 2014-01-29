# Copyright 2013 Isotoma Limited
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

from gevent import Greenlet
from gevent.queue import Queue


class ChangeSet(object):

    def __init__(self, mgr):
        self.mgr = mgr
        self.changes = []

    def bust(self, callable, *args):
        try:
            self.changes.append(self.mgr.executor.get_operation(callable, *args))
        except KeyError:
            pass

    def __enter__(self):
        return self

    def __exit__(self, a, b, c):
        self.mgr.put(self.changes)


class ChangeResponder(object):

    def __init__(self, root):
        self.root = root
        self.executor = root.executor
        self.queue = Queue()

    def changeset(self):
        return ChangeSet(self)

    def put(self, itm):
        if not itm:
            return
        self.queue.put(itm)

    def _run(self):
        print "Started listening for changes"
        for changed in self.queue:
            print "Change occurred"
            for op in changed:
                print " -> Purging '%s' and its rdepends" % op
                op.purge_rdepends()

            print "Requesting resolve"
            self.root.resolve()

    def listen(self):
        return Greenlet.spawn(self._run)
