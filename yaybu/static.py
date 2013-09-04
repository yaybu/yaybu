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

import os
import StringIO
import json

from yaybu.util import args_from_expression
from yaybu import base
from yay import errors
from libcloud.storage.types import Provider, ContainerDoesNotExistError, ObjectDoesNotExistError
from libcloud.storage.providers import get_driver


class StaticContainer(base.GraphExternalAction):

    """
    This part manages a container in a libcloud managed storage provider such
    as S3 or Nimbus

    new StaticContainer as container:
        source: path/to/look/in

        destination:
            id: AWS
            key:
            secret:
            container: container_name
    """

    extra_drivers = {}
    keys = []

    def _get_source_container(self):
        try:
            return self._get_source_container_from_string()
        except errors.TypeError:
            driver_name = self.params.source.id.as_string()
            if driver_name in self.extra_drivers:
                Driver = self.extra_drivers[driver_name]
            else:
                Driver = get_driver(getattr(Provider, driver_name))
            driver = Driver(**args_from_expression(Driver, self.params.source, ignore=("container", )))
            container = driver.get_container(self.params.source.container.as_string())
            return container

    def _get_source_container_from_string(self):
        directory = self.params.source.as_string()
        Driver = get_driver(Provider.LOCAL)
        driver = Driver(os.path.dirname(directory))
        return driver.get_container(os.path.basename(directory))

    def _get_destination_container(self):
        driver_name = self.params.destination.id.as_string()
        if driver_name in self.extra_drivers:
            Driver = self.extra_drivers[driver_name]
        else:
            Driver = get_driver(getattr(Provider, driver_name))
        driver = Driver(**args_from_expression(Driver, self.params.destination, ignore=("container", )))

        container_name = self.params.destination.container.as_string()
        changed = False
        try:
            container = driver.get_container(container_name=container_name)
        except ContainerDoesNotExistError:
            if self.root.readonly:
                return True, None
            with self.root.ui.throbber("Creating container '%s'" % container_name):
                if self.root.simulate:
                    return True, None
                container = driver.create_container(container_name=container_name)
                changed = True
        return changed, container

    def _get_manifest(self, container):
        if container:
            try:
                manifest = container.get_object(".yaybu-manifest")
                return json.loads(''.join(manifest.as_stream()))
            except ObjectDoesNotExistError:
                pass
        return {}

    def _set_manifest(self, container, manifest):
        if not self.root.simulate:
            container.upload_object_via_stream(StringIO.StringIO(json.dumps(manifest)), ".yaybu-manifest")

    def test(self):
        with self.root.ui.throbber("Testing storage credentials/connectivity") as throbber:
            self._get_source_container()
            self._get_destination_container()

    def apply(self):
        if self.root.readonly:
            return

        src = self._get_source_container()
        changed, dest = self._get_destination_container()

        manifest = self._get_manifest(dest)

        source = dict((o.name, o) for o in src.iterate_objects())
        if dest:
            destination = dict((o.name, o) for o in dest.iterate_objects())
        else:
            destination = {}

        source_set = frozenset(source.keys()) - frozenset((".yaybu-manifest", ))
        destination_set = frozenset(destination.keys()) - frozenset((".yaybu-manifest", ))

        to_add = source_set - destination_set
        to_check = source_set.intersection(destination_set)
        to_delete = destination_set - source_set

        # FIXME: Need to dereference object names...
        for name in to_add:
            with self.root.ui.throbber("Uploading new static file '%s'" % name):
                if not self.root.simulate:
                    source_stream = source[name].as_stream()
                    dest.upload_object_via_stream(source_stream, name)
                    manifest[name] = {'source_hash': source[name].hash}
                changed = True

        for name in to_check:
            obj_s = source[name]
            obj_d = destination[name]

            if name in manifest and obj_s.hash == manifest[name]['source_hash']:
                continue

            if obj_s.size == obj_d.size and obj_s.hash == obj_d.hash:
                continue

            with self.root.ui.throbber("Updating static file '%s'" % name):
                if not self.root.simulate:
                    source_stream = obj_s.as_stream()
                    dest.upload_object_via_stream(source_stream, name)
                    manifest[name] = {'source_hash': obj_s.hash}
                changed = True

        for name in to_delete:
            with self.root.ui.throbber("Deleting static file '%s'" % name):
                if not self.root.simulate:
                    destination[name].delete()
                    if name in manifest:
                        del manifest[name]
                changed = True

        self._set_manifest(dest, manifest)

        # HACK ALERT
        self.root.changelog.changed = self.root.changelog.changed or changed
