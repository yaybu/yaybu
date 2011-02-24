=========
Resources
=========

Resources are a core concept in Yaybu.

A Resource is a thing on your deployment target that can be described in
an abstract way and then be managed by Yaybu without any explicit migration
scripts being written. You define the state you want the resource to be in
and yaybu will work out how to get it there.

The management yaybu can range from something like ensure a symbolic link
exists, to applying templates to files, to making sure the right tag
of your Plone site is checked out to anything that can be expressed in
python.

You can recognise when a resource is used in a yay configuration file,
because it will be capitalised.

Filesystem resources
====================

Link
----

.. autoclass:: yaybu.resources.filesystem.Link
.. autoattribute:: yaybu.resources.filesystem.Link.name


Raises
~~~~~~
BinaryMissing
    The system binary for one of the required binaries cannot be found. For    example, ln, rm, chmod etc.
InvalidUser
    The specified `owner` is not a valid unix user.
InvalidGroup
    The specified `group` is not a valid unix group.
OperationFailed
    For an undetermined reason we didn't get a link. This should not happen.
SystemError
    If an error is returned from one of the system calls used.


System Errors
~~~~~~~~~~~~~
 EACCESS
  Search permission is denied on a component of the path prefix
 EEXIST
  `name` already exists
 EIO
  An I/O error occurred
 ELOOP
  Too many symbolic links were encountered in resolving `name` or `to`
 ENAMETOOLONG
  The pathname for `name` or `to` is too long
 ENOENT
  A directory component in oldpath or newpath does not exist or is a dangling symbolic link.
 ENOMEM
  Insufficient kernel memory was available
 ENOSPC
  Insufficient disk space
 ENOTDIR
  A component used as a directory in `name` or `to` is not, in fact, a directory.
 EPERM
  The filesystem containing `name` does not support the creation of symbolic links
 EROFS
  `name` is on a read-only file system


