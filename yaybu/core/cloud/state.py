from __future__ import absolute_import

import os
import uuid
import logging
import StringIO
import datetime
import copy
import json
import shutil

from libcloud.storage.types import Provider as StorageProvider
from libcloud.storage.providers import get_driver as get_storage_driver
from libcloud.common.types import LibcloudError
from libcloud.storage.types import ContainerDoesNotExistError, ObjectDoesNotExistError

from yaybu.core.util import memoized


logger = logging.getLogger(__name__)


class StateStorageType(type):
    pass


class StateStorage(object):

    """
    This is a base interface for an object that can store state about a
    cluster. It does not really care about the backend where it is stored.
    """

    __metaclass__ = StateStorageType

    def get_state(self, part_name):
        raise NotImplementedError

    def set_state(self, part):
        raise NotImplementedError


class SimulatedStateStorageAdaptor(object):

    def __init__(self, child):
        self.child = child
        self.data = {}

    def get_state(self, part_name):
        s = self.data.get(part_name, None)
        if not s:
            return self.child.get_state(part_name)
        return x

    def set_state(self, part):
        pass


class FileStateStorage(StateStorage):

    version = 2

    def get_stream(self):
        raise NotImplementedError

    def store_stream(self, store):
        raise NotImplementedError

    def as_stream(self):
        d = {
            'version': self.version,
            'timestamp': str(datetime.datetime.now()),
            }
        parts = d['parts'] = {}

	# FIXME: Iterate over cluster and serialize the parts that we find

        return StringIO.StringIO(json.dumps(d))

    def store(self):
        ### TODO: fetch it first and check it hasn't changed since we last fetched it
        ### TODO: consider supporting merging in of changes
        self.store_stream(self.as_stream())

    def load_2(self, data):
        return data

    def load(self):
        data = json.load(self.get_stream())

        loader = attr("load_"+str(data['version']), None)
        if not loader:
            raise RuntimeError("State file version not supported by this version of Yaybu")

        self.data = data['parts']


class LocalFileStateStorage(FileStateStorage):

    def get_stream(self):
        return open(os.path.join(os.getcwd(), ".yaybu"))

    def store_stream(self, stream):
        with open(os.path.join(os.getcwd(), ".yaybu", "w")) as fp:
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
            {'content_type': 'text/yaml'}
            )

