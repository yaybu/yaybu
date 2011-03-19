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

"""
Failure Modes
=============

 General failure modes we detect ourselves:
 * Cannot find ln binary
 * Unexpected return code from binary
 * Binary unexpectedly did not create expected symlink
 * User does not exist
 * Group does not exist
 * Template failures


 These are standard C error codes that apply to the underlying calls from these resources.

 * EACCESS Search permission is denied on a component of the path prefix
 * EINVAL mode requested creation of something other than a regular file, device special file, FIFO or socket (mknod only)
 * EIO An I/O error occurred
 * ELOOP To many symbolic links were encountered in resolving pathname
 * EMLINK The file referred to by oldpath already has the maximum number of links to it
 * ENAMETOOLONG The pathname was too long
 * ENFILE The system limit on the total number of open files has been reached
 * ENXIO pathname refers to a device special file and no corresponding device exists
 * ENOENT A directory component in pathname does not exist, or is a dangling symbolic link
 * ENOSPC Insufficient disk space
 * ENOTDIR A component used as a directory in pathname is not in fact a directory
 * EOVERFLOW file is too large to open
 * EPERM The calling process did not have the required permissions
 * EPERM The filesystem does not support the creation of directories
 * EROFS Read only filesystem
 * ETXTBSY pathname refers to an executable image which is currently being executed and write access was requested
 * EXDEV paths are not on the same mounted filesystem (for hardlinks)


 * Above errors for backup file - consider if different reporting needed
 * Disk quota exhausted
 * SELinux Policy does not allow (EPERM or EACCESS?)
 * Insufficient inodes
 * Linked to object does not exist
 * Link name not supported by filesystem
 * Cannot remove existing object (e.g. loopback devices)
 * Stale NFS handles
 * Faulty media
 * Invalid mode
 """

class File(Resource):

    """ A provider for this resource will create or amend an existing file to
    the provided specification.

    For example, the following will create the /etc/hosts file based on a static local file::

        File:
          name: /etc/hosts
          owner: root
          group: root
          mode: 644
          static: my_hosts_file

    The following will create a file using a jinja2 template, and will back up
    the old version of the file if necessary::

        File:
          name: /etc/email_addresses
          owner: root
          group: root
          mode: 644
          template: email_addresses.j2
          template_args:
              foo: foo@example.com
              bar: bar@example.com
          backup: /etc/email_addresses.{year}-{month}-{day}

    """

    name = String()
    """The full path to the file this resource represents."""

    owner = String()
    """A unix username or UID who will own created objects. An owner that
    begins with a digit will be interpreted as a UID, otherwise it will be
    looked up using the python 'pwd' module."""

    group = String()
    """A unix group or GID who will own created objects. A group that begins
    with a digit will be interpreted as a GID, otherwise it will be looked up
    using the python 'grp' module."""

    mode = Octal()
    """A mode representation as an octal. This can begin with leading zeros if
    you like, but this is not required. DO NOT use yaml Octal representation
    (0o666), this will NOT work."""

    static = File()
    """A static file to copy into this resource. The file is located on the
    yaybu path, so can be colocated with your recipes."""

    encrypted = File()
    """A static encrypted file to copy to this resource. The file is located
    on the yaybu path, so can be colocated with your recipe."""

    template = File()
    """A jinja2 template, used to generate the contents of this resource. The
    template is located on the yaybu path, so can be colocated with your
    recipes"""

    template_args = Dict(default={})
    """The arguments passed to the template."""

    backup = String()
    """A fully qualified pathname to which to copy this resource before it is
    overwritten. If you wish to include a date or timestamp, specify format
    args such as {year}, {month}, {day}, {hour}, {minute}, {second}"""

class FileAppliedPolicy(Policy):

    resource = File
    name = "apply"
    default = True
    signature = (Present("name"),
                 NAND(Present("template"),
                      Present("static"),
                      Present("encrypted")),
                 NAND(Present("backup"),
                      Present("dated_backup")),
                 )

class FileRemovePolicy(Policy):

    resource = File
    name = "remove"
    default = False
    signature = (Present("name"),
                 Absent("owner"),
                 Absent("group"),
                 Absent("mode"),
                 Absent("static"),
                 Absent("encrypted"),
                 Absent("template"),
                 Absent("template_args"),
                 NAND(Present("backup"),
                      Present("dated_backup")),
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
