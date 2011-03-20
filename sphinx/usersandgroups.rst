================
Users and Groups
================

User
====

.. automodule:: yaybu.resources.user

.. autoclass:: User()
   :members:

`apply`
-------

.. autoclass:: UserApplyPolicy()

Raises
~~~~~~
:py:exc:`~yaybu.core.error.BinaryMissing`
    The system binary for one of the required binaries cannot be found. For    example, ln, rm, chmod etc.
:py:exc:`~yaybu.core.error.InvalidUser`
    The specified `owner` is not a valid unix user.
:py:exc:`~yaybu.core.error.InvalidGroup`
    The specified `group` is not a valid unix group.
:py:exc:`~yaybu.core.error.OperationFailed`
    For an undetermined reason we didn't get a link. This should not happen.

`remove`
--------

.. autoclass:: yaybu.resources.user.UserRemovePolicy()

NOTE: No providers have been implemented for this policy yet.

Group
=====

.. automodule:: yaybu.resources.group

.. autoclass:: Group()
   :members:


`apply`
-------

.. autoclass:: GroupApplyPolicy()

`remove`
--------

.. todo:: The group remove policy is not yet implemented

