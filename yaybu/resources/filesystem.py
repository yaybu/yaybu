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
    String,
    Integer,
    Octal,
    File,
    Dict,
    )

import stdarg

"""
Failure Modes
=============

 General failure modes we detect ourselves:
 * Cannot find ln binary
 * Unexpected return code from binary
 * Binary unexpectedly did not create expected symlink
 * User does not exist
 * Group does not exist


 * EROFS Read only filesystem
 * ENOSPC Insufficient disk space
 * EACCESS Search permission is denied on a component of the path prefix
 * EPERM The calling process did not have the required permissions
 * EACCESS Write-once media
 * Above errors for backup file - consider if different reporting needed
 * Template failures
 * ELOOP To many symbolic links were encountered in resolving pathname
 * ENOENT A directory component in pathname does not exist, or is a dangling symbolic link
 * Disk quota exhausted
 * ENOTDIR A component used as a directory in pathname is not in fact a directory
 * EPERM The filesystem does not support the creation of directories
 * EIO An I/O error occurred
 * EMLINK The file referred to by oldpath already has the maximum number of links to it
 * ENAMETOOLONG The pathname was too long
 * EXDEV paths are not on the same mounted filesystem (for hardlinks)
 * ENFILE The system limit on the total number of open files has been reached
 * ENXIO pathname refers to a device special file and no corresponding device exists
 * EOVERFLOW file is too large to open
 * ETXTBSY pathname refers to an executable image which is currently being executed and write access was requested
 * EINVAL mode requested creation of something other than a regular file, device special file, FIFO or socket (mknod only)


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
    """

    name = stdarg.name
    owner = stdarg.owner
    group = String()
    mode = Octal()
    static = File()
    template = File()
    template_args = Dict(default={})
    backup = String()
    dated_backup = String()

class FileAppliedPolicy(Policy):

    resource = File
    name = "apply"
    default = True
    signature = (Present("name"),
                 NAND(Present("template"),
                      Present("static")),
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
                 Absent("template"),
                 Absent("template_args"),
                 NAND(Present("backup"),
                      Present("dated_backup")),
                 )

class Directory(Resource):
    name = String()
    owner = String()
    group = String()
    mode = Octal()

class DirectoryAppliedPolicy(Policy):
    resource = Directory
    name = "applied"
    default = True
    signature = (Present("name"),
                 Present("owner"),
                 Present("group"),
                 Present("mode"),
                 )

class DirectoryRemovedPolicy(Policy):
    resource = Directory
    name = "removed"
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
    name = String()
    owner = String()
    group = String()
    to = String()
    mode = Octal()

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
    name = String()
    owner = String()
    group = String()
    mode = Octal()
    type_ = String()
    major = Integer()
    minor = Integer()

class SpecialAppliedPolicy(Policy):
    name = "applied"
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
    name = "removed"
    default = False
    signature = (Present("name"),
                 Absent("owner"),
                 Absent("group"),
                 Absent("mode"),
                 Absent("type_"),
                 Absent("major"),
                 Absent("minor"),
                 )
