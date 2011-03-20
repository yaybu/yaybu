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

""" Resources dealing with filesystem objects other than files. """

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

class Directory(Resource):

    """ A directory on disk. Directories have limited metadata, so this resource is quite limited.

    For example::

        Directory:
          name: /var/local/data
          owner: root
          group: root
          mode: 644

    """

    name = FullPath()
    """ The full path to the directory on disk """

    owner = String()
    """ The unix username who should own this directory """

    group = String()
    """ The unix group who should own this directory """

    mode = Octal()
    """ The octal mode that represents this directory's permissions """

class DirectoryAppliedPolicy(Policy):
    resource = Directory
    name = "apply"
    default = True
    signature = (Present("name"),
                 Present("owner"),
                 Present("group"),
                 Present("mode"),
                 )

class DirectoryRemovedPolicy(Policy):
    resource = Directory
    name = "remove"
    default = False
    signature = (Present("name"),
                 Absent("owner"),
                 Absent("group"),
                 Absent("mode"),
                 )

class DirectoryRemovedRecursivePolicy(Policy):
    resource = Directory
    name = "removed-recursive"
    default = False
    signature = (Present("name"),
                 Absent("owner"),
                 Absent("group"),
                 Absent("mode"),
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

    name = String()
    """The name of the file this resource represents."""

    owner = String()
    """A unix username or UID who will own created objects. An owner that
    begins with a digit will be interpreted as a UID, otherwise it will be
    looked up using the python 'pwd' module."""

    group = String()
    """A unix group or GID who will own created objects. A group that begins
    with a digit will be interpreted as a GID, otherwise it will be looked up
    using the python 'grp' module."""

    to = String()
    """ The pathname to which to link the symlink. Dangling symlinks ARE
    considered errors in Yaybu. """

    mode = Octal()
    """A mode representation as an octal. This can begin with leading zeros if
    you like, but this is not required. DO NOT use yaml Octal representation
    (0o666), this will NOT work."""

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

class Special(Resource):

    """ A special file, as created by mknod. """

    name = FullPath()
    """ The full path to the special file on disk. """

    owner = String()
    """ The unix user who should own this special file. """

    group = String()
    """ The unix group who should own this special file. """

    mode = Octal()
    """ The octal representation of the permissions for this special file. """

    type_ = String()
    """ One of the following strings:

      block
        create a block (buffered) special file
      character
        create a character (unbuffered) special file
      fifo
        create a fifo
    """

    major = Integer()
    """ The major number for the special file. If the type of the special file
    is block or character, then this must be specified. """

    minor = Integer()
    """ The minor number for the special file. If the type of the special file
    is block or character, then this must be specified. """

class SpecialAppliedPolicy(Policy):
    name = "apply"
    default = True
    signature = (Present("name"),
                 Present("owner"),
                 Present("group"),
                 Present("mode"),
                 Present("type_"),
                 Present("major"),
                 Present("minor"),
                 )

class SpecialRemovedPolicy(Policy):
    name = "remove"
    default = False
    signature = (Present("name"),
                 Absent("owner"),
                 Absent("group"),
                 Absent("mode"),
                 Absent("type_"),
                 Absent("major"),
                 Absent("minor"),
                 )
