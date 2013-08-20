.. _runtime_arguments:

=================
Runtime arguments
=================

By setting ``yaybu.options`` you can allow some parts of your configuration to be set at runtime. These are then available in the ``yaybu.argv`` dictionary.


Defining arguments
==================

Strings
-------

The ``string`` argument type is the simplest. You need to specify a ``name`` and can optionally set a ``default``::

    yaybu:
        options:
          - name: username
            type: string
            default: john

A string is actually the default type of argument. So you don't need to specify the ``type``::

    yaybu:
        options:
          - name: username
            default: john


Integer
-------

The ``integer`` argument validates that the argument provided by your end user is indeed a valid integer. It can by defined like this::

    yaybu:
        options:
          - name: num_servers
            type: integer
            default: 1


Boolean
-------

The ``boolean`` argument type takes a value of ``no``, ``0``, ``off`` or ``false`` and interprets it as a negative. ``yes``, ``1``, ``on`` or ``true`` is interpreted as a positive. Other values trigger validation. You can use it like this::

    yaybu:
        options:
          - name: on_off_toggle
            type: boolean
            default: on


Using arguments
===============

The arguments defined via ``yaybu.options`` are available at runtime using the ``yaybu.argv`` mapping.

One use of this is to combine it with the :ref:`Compute <compute>` part to create a configuration that can be deployed multiple times with no changes::

    yaybu:
        options:
          - name: instance
            default: cloud

    new Compute as server:
        name: myproject-{{ yaybu.argv.instance }}
        driver:
            id: EC2
            key: secretkey
            secret: secretsecret
        image: imageid
        size: t1.micro

If i were to run this configuration several times::

    yaybu up
    yaybu up instance=take2
    yaybu up instance=take3

Then i woulld have 3 instances running:

 * ``myproject-cloud``
 * ``myproject-take2``
 * ``myproject-take3``

