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

from yaybu.compute import vbox
from yaybu.compute import bigv
from yaybu.compute import docker
from yaybu.compute import vmware

from .base import Layer

from yay import errors
from yaybu import error

from ..image.library import ImageLibrary

class LocalComputeLayer(Layer):

    drivers = {
        "VMWARE": vmware.VMWareDriver,
        "BIGV": bigv.BigVNodeDriver,
        "DOCKER": docker.DockerNodeDriver,
        "VBOX": vbox.VBoxDriver,
    }

    def __init__(self, original, yaybu_root="~/.yaybu"):
        super(LocalComputeLayer, self).__init__(original)
        self.machines = ImageLibrary(root=yaybu_root)

    def _get_image(self):
        """ Image can look like any one of these three formats:

            image: http://server/path/image.img

            image:
              id: image-id

            image:
              distro: ubuntu
              arch: amd64
              release: 12.04

        """
        try:
            # don't find floats
            params = dict((k, self.params.image.get_key(k).as_string()) for k in self.params.image.keys())
        except errors.NoMatching as e:
            try:
                return self._get_image_from_id('default')
            except error.ValueError:
                pass

            # If the backend doesnt support a 'default' image then raise the
            # original NoMatching exception
            raise e

        except errors.TypeError:
            return self._get_image_from_id(self.params.image.as_string())

        if "id" in params:
            return NodeImage(
                id=params["id"],
                name=self.params.image.name.as_string(default=id),
                extra=params,
                driver=self.driver,
            )
        else:
            id = "{distro}-{release}-{arch}".format(**params)
            return NodeImage(
                id=id,
                name=self.params.image.name.as_string(default=id),
                extra=params,
                driver=self.driver
            )
