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

from __future__ import absolute_import

from yay import errors
from yaybu import base

try:
    import heroku
except ImportError:
    heroku = None


class Heroku(base.GraphExternalAction):

    def __init__(self, params):
        super(Heroku, self).__init__(params)

        if not heroku:
            raise errors.TypeError(
                "Dependency 'heroku' is required and not available", anchor=self.anchor)

        try:
            self.cloud = heroku.from_key(self.params.key.as_string())
        except errors.NoMatching:
            try:
                username = self.params.username.as_string()
                password = self.params.password.as_string()
            except errors.NoMatching:
                raise errors.TypeError(
                    "Must specify key or username and password", anchor=self.params.anchor)
            self.cloud = heroku.from_pass(username, password)

    def action(self, msg):
        print msg

    def apply(self):
        if self.root.readonly:
            return

        changed = False

        app_id = self.params.application_id.as_string()
        if not app_id in self.cloud.apps:
            self.action("Creating new app named '%s'" % app_id)
            if not self.root.simulate:
                self.app = self.cloud.apps.add(app_id)
            else:
                self.app = None
            changed = True

        else:
            self.app = self.cloud.apps[app_id]

        self.action("Entering maintenance mode")
        if not self.root.simulate and self.app:
            self.app.maintenance(on=True)

        self.apply_configuration()
        self.apply_scaling()
        self.apply_addons()

        self.action("Leaving maintenance mode")
        if not self.root.simulate and self.app:
            self.app.maintenance(on=False)

        self.apply_domains()

        # May generate e-mail so do it last - we don't want someone looking
        # half way through set up
        self.apply_collaborators()

        self.root.changelog.changed = changed

    def apply_collaborators(self):
        collaborators = self.app.collaborators if self.app else []
        old_state = set(c.email for c in collaborators)
        new_state = set(self.params.collaborators.as_iterable(default=[]))

        for collaborator in (new_state - old_state):
            self.action("Adding collaborator '%s'" % collaborator)
            if self.app and not self.root.simulate:
                self.app.collaborators.add(collaborator)

        for collaborator in (old_state - new_state):
            self.action("Removing collaborator '%s'" % collaborator)
            if self.app and not self.root.simulate:
                self.app.collaborators[collaborator].delete()

    def apply_domains(self):
        domains = self.app.domain if self.app else []
        old_domains = set(d.domain for d in domains)
        new_domains = set(self.params.domains.as_iterable(default=[]))

        for domain in (new_domains - old_domains):
            self.action("Adding domain name '%s'" % domain)
            if self.app and not self.root.simulate:
                self.app.domains.new(domain)

        for domain in (old_domains - new_domains):
            self.action("Removing domain name '%s'" % domain)
            if self.app and not self.root.simulate:
                self.app.domains[domain].delete()

    def apply_addons(self):
        """
        Compare the state of addons to the requested state of addons and update
        as needed.

        Addons are specified in the form ``type:tier`` (the docs say type:name).

        Upgrading is supported - so we have to capture foo:basic ->
        foo:advanced rather than deleting advanced and adding basic.

        Because of this. currently this code assumes their won't be duplicate
        add-ons (e.g. foo:basic won't be present at same time as foo:advanced).
        """
        old_addons = [a for a in self.app.addons]
        old_addons_by_type = dict((a.type, a.name) for a in old_addons)
        # assert len(old_addons) == len(old_addons_by_type)

        new_addons_by_type = dict((a.split(":", 1)[0], a)
                                  for a in self.params.addons.as_iterable(default=[]))
        # assert len(self.get('addons', [])) == len(new_addons_by_type)

        old_state = set(old_addons_by_type.keys())
        new_state = set(new_addons_by_type.keys())

        # Change tiers
        for addon_type in new_state.intersection(old_state):
            new_addon = new_addons_by_type[addon_type]
            old_addon = old_addons_by_type[addon_type]
            if new_addon != old_addon:
                self.action("Upgrading addon from '%s' to '%s'" %
                            (old_addon, new_addon))
                if not self.root.simulate:
                    self.app.addons[old_addon].upgrade(new_addon)

        # Add new addons
        for addon_type in (new_state - old_state):
            addon = new_addons_by_type[addon_type]
            self.action("Adding new add-on '%s'" % addon)
            if not self.root.simulate:
                self.app.addons.add(addon)

        # Remove old addons
        for addon_type in (old_state - new_state):
            addon = old_addons_by_type[addon_type]
            self.action("Removing add-on '%s'" % addon)
            if not self.root.simulate:
                self.app.addons[addon].delete()

    def apply_scaling(self):
        try:
            after = self.params.dynos.keys()
        except errors.NoMatching:
            after = []

        for dyno in after:
            if not self.app or not dyno in self.app.processes:
                raise ExecutionError(
                    "Tried to configure dyno '%s' but it doesn't exist in the app" % dyno)

        for dyno in after:
            scale = self.params.dynos[dyno].as_int()
            current_scale = len(self.app.processes[dyno])
            if current_scale != scale:
                self.action("Scaling dyno '%s' from %d workers to %d workers" %
                            (dyno, current_scale, scale))
                if self.app and not self.root.simulate:
                    self.app.processes.scale(scale)

        current_dynos = self.app.releases[
            -1].pstable.keys() if self.app else []
        for dyno in current_dynos:
            if dyno not in after:
                self.action(
                    "Stopping all dyno for '%s' as not known by Yaybu" % dyno)
                if self.app and not self.root.simulate:
                    self.app.processes.scale(0)

    def apply_configuration(self):
        config = self.app.config.data.keys() if self.app else []
        before = set(config)
        try:
            current = set(self.params.config.keys())
        except errors.NoMatching:
            current = set()

        # Check for modifications
        for key in before.intersection(current):
            var = self.params.config[key].as_string()
            if self.app.config[key] != var:
                self.action("Updating configuration variable '%s'" % key)
                if not self.root.simulate:
                    self.app.config[key] = var

        # Check for new configuration
        for key in (current - before):
            self.action("Adding new configuration variable '%s'" % key)
            if not self.root.simulate:
                self.app.config[key] = self.params.config[key].as_string()

        # Config that was removed - we can't really delete this config as we
        # don't know if its something an addon put there
        # for var in (before - current):
        #     log.warning("Config variable '%s' present on Heroku but not configuration managed")
