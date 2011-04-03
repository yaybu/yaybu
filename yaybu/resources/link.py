# Copyright 2011 Isotoma Limited
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

""" Resources representing symbolic links. """

from yaybu.core.resource import Resource
from yaybu.core.policy import (Policy,
                               Absent,
                               Present,
                               XOR,
                               NAND)

from yaybu.core.argument import (
    FullPath,
    String,
    Integer,
    Octal,
    File,
    Dict,
    )


class Link(Resource):

    """ A resource representing a symbolic link. The link will be from `name`
    to `to`. If you specify owner, group and/or mode then these settings will
    be applied to the link itself, not to the object linked to.

    For example::

      Link:
        name: /etc/init.d/exampled
        to: /usr/local/example/sbin/exampled
        owner: root
        group: root

    """

    name = FullPath()
    """The name of the file this resource represents."""

    owner = String(default="root")
    """A unix username or UID who will own created objects. An owner that
    begins with a digit will be interpreted as a UID, otherwise it will be
    looked up using the python 'pwd' module."""

    group = String(default="root")
    """A unix group or GID who will own created objects. A group that begins
    with a digit will be interpreted as a GID, otherwise it will be looked up
    using the python 'grp' module."""

    to = FullPath()
    """ The pathname to which to link the symlink. Dangling symlinks ARE
    considered errors in Yaybu. """

class LinkAppliedPolicy(Policy):
    resource = Link
    name = "apply"
    default = True
    signature = (
        Present("name"),
        Present("to"),
        )


class LinkRemovedPolicy(Policy):
    resource = Link
    name = "remove"
    default = False
    signature = (
        Present("name"),
        Absent("to"),
        )

