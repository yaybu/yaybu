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
import logging
import StringIO
import datetime
import json
import shutil
from abc import ABCMeta

from libcloud.storage.types import Provider as StorageProvider
from libcloud.storage.providers import get_driver as get_storage_driver
from libcloud.storage.types import ContainerDoesNotExistError, ObjectDoesNotExistError

from yaybu.core.util import memoized

logger = logging.getLogger(__name__)

class PartState(object):

    def __init__(self, state, partid):
        self.state = state
        self.partid = partid
        self.data = {}

    def refresh(self):
        self.data = self.state.get_state(self.partid)

    def update(self, **kwargs):
        self.refresh()
        self.data.update(kwargs)
        self.state.set_state(self.partid, self.data)

    def keys(self):
        return self.data.keys()

    def __contains__(self, key):
        return key in self.data

    def __getitem__(self, key):
        return self.data[key]

    def __getattr__(self, key):
        try:
            return self.data[key]
        except KeyError:
            raise AttributeError(key)


class StateStorageType(ABCMeta):

    """ Registers the provider with the resource which it provides """

    types = {}

    def __new__(meta, class_name, bases, new_attrs):
        cls = super(StateStorageType, meta).__new__(meta, class_name, bases, new_attrs)
        if new_attrs.get("concrete", True):
            meta.types[new_attrs.get("name", class_name.lower())] = cls
        if "concrete" in new_attrs:
            del new_attrs['concrete']
        return cls


class StateStorage(object):

    """
    This is a base interface for an object that can store state about a
    cluster. It does not really care about the backend where it is stored.
    """

    __metaclass__ = StateStorageType
    concrete = False

    def get_state(self, part_name):
        raise NotImplementedError

    def set_state(self, part_name, state):
        raise NotImplementedError


class SimulatedStateStorageAdaptor(StateStorage):

    concrete = False

    def __init__(self, child):
        logger.debug("Wrapping state storage in read-only adaptor")
        self.child = child
        self.data = {}

    def get_state(self, part_name):
        s = self.data.get(part_name, None)
        if not s:
            return self.child.get_state(part_name)
        return x

    def set_state(self, part_name, state):
        pass


class FileStateStorage(StateStorage):

    version = 2

    def get_state(self, part_name):
        self.load()
        return self.data.get(part_name, {})

    def set_state(self, part_name, state):
        self.data[part_name] = state
        self.store()

    def get_stream(self):
        raise NotImplementedError

    def store_stream(self, store):
        raise NotImplementedError

    def as_stream(self):
        d = {
            'version': self.version,
            'timestamp': str(datetime.datetime.now()),
            'parts': self.data,
            }
        return StringIO.StringIO(json.dumps(d, indent=4))

    def store(self):
        ### TODO: fetch it first and check it hasn't changed since we last fetched it
        ### TODO: consider supporting merging in of changes
        self.store_stream(self.as_stream())

    def load_2(self, data):
        return data

    def load(self):
        stream = self.get_stream()

        if not stream:
            self.data = {}
            return

        data = json.load(self.get_stream())

        if not 'version' in data:
            raise RuntimeError("State file has no version metadata - possible corrupt")

        loader = getattr(self, "load_"+str(data['version']), None)
        if not loader:
            raise RuntimeError("State file version not supported by this version of Yaybu")

        self.data = data.get('parts', {})


class LocalFileStateStorage(FileStateStorage):

    def get_stream(self):
        path = os.path.join(os.getcwd(), ".yaybu")
        if not os.path.exists(path):
            return None
        return open(path)

    def store_stream(self, stream):
        with open(os.path.join(os.getcwd(), ".yaybu"), "w") as fp:
            shutil.copyfileobj(stream, fp)


class CloudFileStateStorage(FileStateStorage):

    state_bucket = "yaybu-state"

    @property
    @memoized
    def driver(self):
        self.driver_name = self.args['id']
        del self.args['id']
        provider = getattr(StorageProvider, self.driver_name)
        driver_class = get_storage_driver(provider)
        return driver_class(**self.driver_args)

    def get_container(self, name):
        try:
            container = self.driver.get_container(container_name=name)
        except ContainerDoesNotExistError:
            container = self.driver.create_container(container_name=name)
        return container

    def get_stream(self):
        """ Load the state file from the cloud """
        logger.debug("Loading state from bucket")
        container = self.get_container(self.state_bucket)
        try:
            bucket = container.get_object(self.cluster.name)
            return bucket.as_stream()
        except ObjectDoesNotExistError:
            raise RuntimeError("Object does not exist")

    def store_stream(self, stream):
        """ Store the state in the cloud """
        logger.debug("Storing state")
        container = self.get_container(self.state_bucket)
        container.upload_object_via_stream(
            stream,
            self.cluster.name,
            {'content_type': 'application/json'}
            )

