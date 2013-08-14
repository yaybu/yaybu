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

