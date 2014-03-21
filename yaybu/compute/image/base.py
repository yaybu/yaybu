# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import abc
import urllib2
import logging

from . import error

logger = logging.getLogger("image")


class CloudImage(object):

    """ Represents a cloud image file for a specified release and
    architecture, with a local manifestation of the image. If no image exists
    locally it is fetched from the source provided by the distribution. e"""

    __metaclass__ = abc.ABCMeta

    # size of blocks fetched from remote resources
    blocksize = 81920

    def __init__(self, directory, release, arch):
        self.directory = directory
        self.release = release
        self.arch = arch
        self.remote_hash = None
        self.local_hash = None

    @abc.abstractproperty
    def hash_function(self):
        """ The hash function used to hash local files """

    @abc.abstractmethod
    def remote_image_url(self):
        """ Return a complete url of the remote virtual machine image """

    @abc.abstractmethod
    def remote_hashfile_url(self):
        """ Return a complete url of the remote hash file that contains the
        hash for the virtual machine image. Return None if no hash file is
        available. """

    @abc.abstractmethod
    def filename_prefix(self):
        """ The first part of the filename, used for every file on disk
        locally, such as disk images, specification files, buffers etc.
        within the VM directory """

    @abc.abstractmethod
    def image_hash(self, hashes):
        """ From the dictionary of all hashes provided in the remote hash
        file, return the hash of the virtual machine image """

    def local_filename(self, extension):
        return self.filename_prefix() + extension

    def local_pathname(self, extension):
        return os.path.join(self.directory, self.local_filename(extension))

    def local_image_filename(self):
        return self.local_filename(".img")

    def local_image_pathname(self):
        return self.local_pathname(".img")

    def fetch(self):
        remote_url = self.remote_image_url()
        pathname = self.local_image_pathname()
        logger.info("Retrieving {0} to {1}".format(remote_url, pathname))
        try:
            response = urllib2.urlopen(remote_url)
        except urllib2.HTTPError:
            raise error.CloudInitException("Unable to fetch {0}".format(remote_url))
        local = open(pathname, "w")
        while True:
            data = response.read(self.blocksize)
            if not data:
                break
            local.write(data)

    def decode_hashes(self, data):
        hashes = {}
        for line in data.splitlines():
            parts = line.strip().split()
            if len(parts) == 2:
                hashes[parts[1]] = parts[0]
        return hashes

    def get_remote_hashes(self):
        remote_url = self.remote_hashfile_url()
        logger.info("Fetching hashes from {0}".format(remote_url))
        try:
            response = urllib2.urlopen(remote_url)
        except urllib2.HTTPError:
            return {}
        return self.decode_hashes(response.read())

    def get_local_sum(self):
        pathname = self.local_image_pathname()
        h = self.hash_function()
        if os.path.exists(pathname):
            h.update(open(pathname).read())
            return h.hexdigest()

    def update_hashes(self):
        if self.remote_hash is None:
            self.remote_hash = self.image_hash(self.get_remote_hashes())
        self.local_hash = self.get_local_sum()

    def requires_update(self):
        if self.local_hash is None:
            logger.info("Image not present locally, fetching")
            return True
        elif self.local_hash != self.remote_hash:
            logger.info("Local image does not match remote sum, fetching")
            return True
        else:
            logger.info("Sums match for local image, not updating")
            return False

    def update(self):
        self.update_hashes()
        if self.requires_update():
            self.fetch()
        self.update_hashes()
        if self.requires_update():
            logger.error("Local image sum {0} does not match remote {1} after fetch.".format(self.local_hash, self.remote_hash))
            raise error.FetchFailedException("Local image missing or wrong after fetch")

    #def make_vmx(self):
        #source = self.local_image_filename()
        #vmdk = self.local_filename(".vmdk")
        #vmx = self.local_filename(".vmx")
        #converter = conversion.ImageConverter(self.directory)
        #converter.convert_image(source, vmdk, "vmdk")
        #converter.create_plain_vmx(vmx, vmdk)


class StandardCloudImage(CloudImage):

    def remote_image_url(self):
        url = self.source + "/" + self.prefix + self.image_suffix
        return url.format(server=self.server,
                          release=self.release,
                          arch=self.arch)

    def remote_hashfile_url(self):
        url = self.source + "/" + self.checksums
        return url.format(server=self.server,
                          release=self.release,
                          arch=self.arch)

    def filename_prefix(self):
        return self.prefix.format(release=self.release, arch=self.arch)

    def image_hash(self, hashes):
        template = "*" + self.prefix + self.image_suffix
        filename = template.format(release=self.release, arch=self.arch)
        return hashes.get(filename, None)
