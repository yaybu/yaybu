===========================
Hacking and extending Yaybu
===========================

Information for those wishing to write their own providers, or add new classes of resource.

Unicode
=======

Your provider methods will be called with unicode arguments. Make sure you can
handle unicode appropriately - in general these days that means serialising to
UTF-8 when interacting with the environment outside the interpreter.

Resources
=========

Resources are a core concept in Yaybu. You can recognise when a resource is
used in a yay configuration file, because it will be capitalised.

All resources inherit from :class:`yaybu.core.resource.Resource`.

.. autoclass:: yaybu.core.resource.Resource

