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

from yaybu.core.util import memoized
from yaybu.util import args_from_expression
from yaybu import base
from yay import ast, errors
from libcloud.storage.types import Provider, ContainerDoesNotExistError
from libcloud.storage.providers import get_driver
from libcloud.common.types import LibcloudError


class StaticContainer(base.GraphExternalAction):

    """
    This part manages a container in a libcloud managed storage provider such
    as S3 or Nimbus

    new StaticContainer as container:
        driver:
            id: AWS
            key:
            secret:

        container: container_name
        directory: path/to/look/in
    """

    keys = []

    def _get_source_container(self):
        directory = self.params.directory.as_string()

        Driver = get_driver(Provider.LOCAL)
        driver = Driver(os.path.dirname(directory))
        return driver.get_container(os.path.basename(directory))

    @property
    @memoized
    def driver(self):
        driver_name = self.params.driver.id.as_string()
        Driver = get_driver(getattr(Provider, driver_name))
        driver = Driver(**args_from_expression(Driver, self.params.driver))
        return driver

    def _get_container(self):
        container_name = self.params.container.as_string()
        changed = False
        try:
            container = self.driver.get_container(container_name=container_name)
        except ContainerDoesNotExistError:
            with self.root.ui.throbber("Creating container '%s'" % container_name):
                container = self.driver.create_container(container_name=container_name)
                changed = True
        return changed, container

    def test(self):
        with self.root.ui.throbber("Testing DNS credentials/connectivity") as throbber:
            self.driver.list_containers()

    def apply(self):
        if self.root.readonly:
            return

        src = self._get_source_container()
        changed, dest = self._get_container()

        source = dict((o.name, o) for o in src.iterate_objects())
        destination = dict((o.name, o) for o in dest.iterate_objects())

        source_set = frozenset(source.keys())
        destination_set = frozenset(destination.keys())

        to_add = source_set - destination_set
        to_check = source_set.intersection(destination_set)
        to_delete = destination_set - source_set

        # FIXME: Need to dereference object names...
        for name in to_add:
            with self.root.ui.throbber("Uploading new static file '%s'" % name):
                source_stream = source[name].as_stream()
                dest.upload_object_via_stream(source_stream, name)
                changed = True

        for name in to_check:
            obj_s = source[name]
            obj_d = destination[name]

            if obj_s.size == obj_d.size and obj_s.hash == obj_d.hash:
                continue

            with self.root.ui.throbber("Updating static file '%s'" % name):
                source_stream = obj_s.as_stream()
                dest.upload_object_via_stream(source_stream, name)
                changed = True

        for name in to_delete:
            with self.root.ui.throbber("Deleting static file '%s'" % name):
                destination[name].delete()
                changed = True

        # HACK ALERT
        self.root.changelog.changed = self.root.changelog.changed or changed
