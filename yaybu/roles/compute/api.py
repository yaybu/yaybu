# Copyright 2012 Isotoma Limited
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

#####################################################################
# Monkeypatch httplib so that libcloud doesn't hang on get_object
# This is only needed on python 2.6 but should be safe for other pythons
# (This fix is now upstream in libcloud, we should dep on it ASAP)
import httplib
HTTPResponse = httplib.HTTPResponse

class HTTPResponse27(HTTPResponse):

    def read(self, amt=None):
        if self.fp is None:
            return ''
        if self._method == 'HEAD':
            self.close()
            return ''
        return HTTPResponse.read(self, amt)

httplib.HTTPResponse = HTTPResponse27
httplib.HTTPConnection.response_class = HTTPResponse27
#####################################################################

import libcloud.security
libcloud.security.VERIFY_SSL_CERT = False
libcloud.security.VERIFY_SSL_CERT_STRICT = False

from libcloud.storage.types import Provider as StorageProvider

from libcloud.storage.providers import get_driver as get_storage_driver

from libcloud.common.types import LibcloudError
from libcloud.storage.types import ContainerDoesNotExistError

import os
import uuid
import logging
import yaml
import StringIO
import datetime
import collections
import time

from yaybu.core.util import memoized
from yaybu.core import remote

logger = logging.getLogger(__name__)

max_version = 1


class Cloud(object):

    """ Adapter of a cloud that provides access to runtime functionality. """

    def __init__(self, storage_provider, dns_provider, args=(), storage_args=()):
        """ storage_args and compute_args will be used for preference if
        provided. otherwise args are used for both """
        self.storage_provider = storage_provider
        self.args = dict(args)
        self.storage_args = dict(storage_args) or self.args
    
    @property
    @memoized
    def storage(self):
        provider = getattr(StorageProvider, self.storage_provider)
        driver_class = get_storage_driver(provider)
        return driver_class(**self.storage_args)
    
    def get_container(self, name):
        try:
            container = self.storage.get_container(container_name=name)
        except ContainerDoesNotExistError:
            container = self.storage.create_container(container_name=name)
        return container

