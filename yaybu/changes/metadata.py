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


from .base import Change


#class Record(object):
#
#    def __init__(self, id, metadata):
#        self.id = id
#        self.metadata = metadata
#
#    def match(self, record):
#        return self.id == record.id
#
#    def diff(self, record):
#        diffs = []
#        for k in self.metadata.keys():
#            if self.metadata[k] != record.metadata[k]:
#                diffs.append(k, self.metadata[k], record.metadata[k])


class MetadataSync(Change):

    """
    I am an abstract Change implementation for tasks that involving
    synchronisng 2 simple CRUD systems (where 1 is yay graph data).
    """

    purge_remote = True
    changed = False

    def get_local_records(self):
        raise NotImplementedError

    def get_remote_records(self):
        raise NotImplementedError

    def match_local_to_remote(self, local, remotes):
        return None

    def add(self, record):
        raise NotImplementedError

    def update(self, uid, record):
        raise NotImplementedError

    def delete(self, uid, record):
        raise NotImplementedError

    def apply(self, ctx, renderer):
        remote = list(self.get_remote_records())
        remote_lookup = dict(r for r in remote)

        local = list(self.get_local_records())
        local_lookup = dict(r for r in local)

        for rid, record in local:
            uid = self.match_local_to_remote(record, remote_lookup)
            rid = uid or rid

            if not rid in remote_lookup:
                with ctx.root.ui.throbber("Adding '%s'" % rid) as throbber:
                    self.changed = True
                    if not ctx.simulate:
                        self.add(record)
                    continue

            if record != remote_lookup[rid]:
                with ctx.root.ui.throbber("Updating '%s'" % rid) as throbber:
                    self.changed = True
                    if not ctx.simulate:
                        self.update(rid, record)
                    continue

            # renderer.debug("'%s' not changed" % rid)

        if self.purge_remote:
            for rid, record in remote:
                if not rid in local_lookup:
                    with ctx.root.ui.throbber("Deleting '%s'" % rid) as throbber:
                        self.changed = True
                        if not ctx.simulate:
                            self.delete(rid, record)

        return self
