==========================
Other filesystem resources
==========================

.. automodule:: yaybu.resources.filesystem

Directory
=========

.. autoclass:: Directory()
   :members:

`apply`
-------

`remove`
--------

Link
====

.. autoclass:: Link()
   :members:

`apply`
-------

Create or change the symbolic link.

Raises
######
:py:exc:`~yaybu.core.error.BinaryMissing`
    The system binary for one of the required binaries cannot be found. For    example, ln, rm, chmod etc.
:py:exc:`~yaybu.core.error.InvalidUser`
    The specified `owner` is not a valid unix user.
:py:exc:`~yaybu.core.error.InvalidGroup`
    The specified `group` is not a valid unix group.
:py:exc:`~yaybu.core.error.DanglingSymlink`
    The destination of the symbolic link does not exist.
:py:exc:`~yaybu.core.error.OperationFailed`
    For an undetermined reason we didn't get a link. This should not happen.
:py:exc:`~yaybu.core.error.SystemError`
    If an error is returned from one of the system calls used.

System Errors
#############
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

Special
=======

.. autoclass:: Special()
   :members:

`apply`
-------

`remove`
--------

