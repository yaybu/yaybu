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

""" Resources representing mount points. """

from yaybu.provisioner.resource import Resource
from yaybu.core.policy import Policy, Present
from yaybu.core.argument import (
    Property,
    FullPath,
    String,
    )


class Mount(Resource):

    name = Property(FullPath)
    """The name of the file this resource represents."""

    """ The type of mount e.g. ext3 """
    fs_type = Property(String)

    """ The options to pass to mount """
    options = Property(String, default="defaults")

    device = Property(FullPath)
    """ The pathname to which to link the symlink. Dangling symlinks ARE
    considered errors in Yaybu. """


class MountPolicy(Policy):
    resource = Mount
    name = "apply"
    default = True
    signature = (
        Present("name"),
        Present("fs_type"),
        Present("device"),
        )

