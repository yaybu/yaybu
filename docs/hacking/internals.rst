=========
Internals
=========

Resources
=========

Resources are a core concept in Yaybu. You can recognise when a resource is
used in a yay configuration file, because it will be capitalised.

All resources inherit from :class:`yaybu.core.resource.Resource`.

.. autoclass:: yaybu.core.resource.Resource

If your custom package implements new resources you can include them using
entry points. Add an ``entry_points`` to your setup.py::

    setup(
        name='MyCustomResources',
        entry_points="""
           [yaybu.resources]
           resources = my.package.resources
           """,
        )

The ``my.package.resources`` module should import any resources you want
to register.


Policies
========

A resource doesn't do anything by itself. A policy declares how a resource
should be managed. A typical policy we define is 'apply'. This makes sure
all the settings declared in the resource are applied to the resource.
Another common one is 'remove'.


Providers
=========

Providers are the classes that actually do things. There might be multiple
providers that provide the same policy for the same resource. For example,
an apt and yum provider will both provide "install" for the Package resource.

If your custom package implements new providers you can include them using
entry points. Add an ``entry_points`` to your setup.py::

    setup(
        name='MyCustomProviders',
        entry_points="""
           [yaybu.providers]
           providers = my.package.providers
           """,
        )

The ``my.package.providers`` module should import any providers you want
to register.


Unicode
=======

Your provider methods will be called with unicode arguments. Make sure you can
handle unicode appropriately - in general these days that means serialising to
UTF-8 when interacting with the environment outside the interpreter.


