================
Users and Groups
================

User
====

.. autoclass:: yaybu.resources.user.User
   :members:

Policies
--------

The following policies are available for users.

Apply
~~~~~

.. autoclass:: yaybu.resources.user.UserApplyPolicy

Raises
######
BinaryMissing
    The system binary for one of the required binaries cannot be found. For    example, ln, rm, chmod etc.
InvalidUser
    The specified `owner` is not a valid unix user.
InvalidGroup
    The specified `group` is not a valid unix group.
OperationFailed
    For an undetermined reason we didn't get a link. This should not happen.

Remove
~~~~~~

.. autoclass:: yaybu.resources.user.UserRemovePolicy

NOTE: No providers have been implemented for this policy yet.

Group
=====

.. py:module:: yaybu.resources.group

.. autoclass:: Group
   :members:


Policies
--------

Apply
~~~~~
