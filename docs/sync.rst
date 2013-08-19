.. _staticcontainer:

======================================
Syncing static files to cloud services
======================================

The ``StaticContainer`` part allows static assets to be synchronised from one container to another. The primary use case is to upload assets from your local drive to the cloud.

A simple invocation looks like this::

    new StaticContainer as my_static_files:
        source: local/path

        destination:
            id: S3
            key: yourawskey
            secret: yourawssecret
            container: target_container

This will sync the contents of a local folder to a destination container.

If the source and destination have incompatible approaches to hashing ``StaticContainer`` will automatically generate and store a manifest in the target destination.

Any service that can be used as a destination can also be used as a source, so this also works::

    new StaticContainer as my_static_files:
        source:
            id: S3
            key: yourawskey
            secret: yourawssecret
            container: source_container

        destination:
            id: S3
            key: yourawskey
            secret: yourawssecret
            container: target_container


Options
=======

There are 2 main options for ``StaticContainer``. The ``source`` and ``destination``.

``source`` can either be a simple string with a path to local files or it can describe a libcloud driver::

    source:
        id: S3
        key: yourawskey
        secret: yourawssecret
        container: source_container

The ``destination`` must be a set of driver parameters as above.

The exact options vary based on the driver that you use, and this is covered in more detail below.


Supported drivers
=================

Using libcloud to implement this part allows us to support a number of DNS services. Some of these receive more extensive real world testing than others and are listed in this section.

Local files
-----------

You can synchronise from and to any folder that is accessible locally use the ``LOCAL`` driver::

    new StaticContainer as my_static_files:
        source: ~/source

        destination:
            id: LOCAL
            key: yourawskey
            secret: yourawssecret
            container: target_container


S3
--

The driver id for S3 is ``S3``::

    new StaticContainer as my_static_files:
        source: ~/source

        destination:
            id: S3
            key: yourawskey
            secret: yourawssecret
            container: target_container



Community supported drivers
===========================

By using libcloud to support the services in the previous section, the following services are also available:

Azure Blobs
-----------

CloudFiles
----------

Google Storage
--------------

Nimbus
------

Ninefold
--------

