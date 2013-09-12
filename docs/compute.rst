.. _compute:

=================
Compute instances
=================

The ``Compute`` part can be used to create and destroy services in various
cloud services supported by libcloud as well as various local VM tools.

Creating a simple compute node will look something like this::

    new Compute as server:
        name: test123456

        driver:
            id: BIGV
            key: yourusername
            secret: yourpassword
            account: youraccountname

        image: precise

        user: root
        password: aez5Eep4

In this example we are creating a server via `BigV <http://www.bigv.io/>`_, but
because our cloud support is underpinned by libcloud we support many hosting
providers.


Options
=======

Any compute instances you create must have a unique ``name``. This lets yaybu keep track of it between ``yaybu apply`` invocations.

Use the ``driver`` argument to configure a libcloud driver for your hosting service. Specific driver sub arguments are discussed in the sections below.

You can choose an base image using the ``image`` argument. For the common case an image id is enough::

    new Compute as server:
        image: ami-f7445d83

You can choose an instance ``size`` by passing a size name::

    new Compute as server:
        size: t1.micro

Some servers don't have the concept of size but you can control the resources assigned in a more granular way::

    new Computer as server:
        size:
            processors: 5

See the driver specific options below for more information on what tweaks you can pass to a backend.

You must choose a ``username`` that can be used to log in with.

If you provide a ``public_key`` file and are using a driver that supports it Yaybu will automatically load it into the created instance to enable key based authentication.

If you provide a ``password`` and the backend supports it then Yaybu will automatically set the account password for the newly created instance.

The ``Compute`` part does not look at the ``private_key`` attribute, but as it is common to use the ``Compute`` part directly with a ``Provisioner`` part, which does check for it, you will often see it specified::

    new Provisioner as vm1:
        new Compute as server:
            private_key: path/to/privatekey


Supported services
==================

BigV
----

Our `BigV <http://www.bigv.io/>`_ support is implemented via `the libcloud 
library <https://github.com/apache/libcloud>`_ but is currently residing in
the Yaybu codebase. As you can set the password for an instance when it is
created there is no preparation to do to create a bigv instance, other than
creating a bigv account.

Your ``Yaybufile`` looks like this::

    new Provisioner as vm1:
        new Compute as server:
            name: test123456

            driver:
                id: BIGV
                key: yourusername
                secret: yourpassword
                account: youraccountname

            image: precise

            user: root
            password: aez5Eep4

        resources:
          - Package:
              name: git-core

This example will create a new vm called ``test123456``. You will be able to
log in as root using the password ``aez5Eep4`` (though you should use ``pwgen``
to come up with something better).


EC2
---

Provisioning of AWS instances is supported out of the box using libcloud.
You will need to have set up an SSH key in the Amazon control panel and either
have the path to the private part of that key or have added it to your
ssh-agent.

You'll need something like this in your ``Yaybufile``::

    new Compute as server:
        name: myappserver

        driver:
            id: EC2_EU_WEST
            key: mykey
            secret: mysecret

        size: t1.micro
        image: ami-4f504f3b

        user: ubuntu
        ex_keyname: mykey
        private_key: mykey.pem


``ex_keyname`` is the name of the SSH key pair in the amazon console.
``private_key`` is the corresponding private key.

We recently merged a patch upstream to do away with ``ex_keyname``. In future Yaybu will be able to automatically upload a ``public_key`` for you in the same way it can for other backends.


VMWare
------

You'll need a copy of VMWare Workstation, VMWare Fusion or VMWare Player.
You'll need a base image to use. My checklist when creating mine is:

* Is ``openssh-server`` installed?
* Is there a user with passphraseless sudo access to root?
* Have I deleted the /etc/udev/rules.d/70-persistent-net.rules?

When you are done, shut down the VM and get the path to its VMX file.

Now your ``Yaybufile`` looks like this::

    new Compute as server:
        name: mytest vm
        driver: VMWARE

        image:
            id: ~/vmware/ubuntu/ubuntu.vmx

        user: ubuntu


Community supported services
============================

By using libcloud to support the services in the previous section, the following services are also available. Please adopt your favourite and help improve documentation for it.

Cloudstack
----------

The driver id for `CloudStack <http://cloudstack.apache.org/>`_ is ``CLOUDSTACK``::

    new Compute as server:
        name: new_cloudstack_server

        driver:
            id: CLOUDSTACK
            host: yourcloudstackhost.com
            path: /api/2.0
            key: yourkey
            secret: yoursecret

        image: yourimageid
        size: yoursizeid

.. note:: The CloudStack libcloud driver could be updated to allow the user to inject SSH keys, but this is not currently in progress.


Digital Ocean
-------------

The driver if for `Digital Ocean <http://www.digitalocean.com>`_ is ``DIGITAL_OCEAN``::

    new Compute as server:
        name: new_digital_ocean_server

        driver:
            id: DIGITAL_OCEAN
            key: yourkey
            secret: yoursecret

        image: yourimageid
        size: yoursizeid

.. note:: The Digitial Ocean libcloud driver could be updated to allow the user to inject SSH keys, but this is not currently in progress.


Gandi
-----

The driver id for `Gandi <http://www.gandi.net>`_ is ``GANDI``::

    new Compute as server:
        name: new_gandi_server

        driver:
            id: GANDI
            key: yourkey
            secret: yoursecret

        image: yourimageid
        size: yoursizeid


GoGrid
------

IBM SCE
-------

Linode
------

OpenStack
---------

Rackspace
---------

SoftLayer
---------

And more
--------

The libcloud project supports `a lot <http://libcloud.apache.org/docs/compute/supported_providers.html>`_ of compute services. The goal is that any cloud service supported by libcloud can be controlled using Yaybu, and any fixes to improve that support will be pushed upstream.


Adding support for your other hosting services
==============================================

Depending on what you are doing there are different requirements.

If you have prepepared images and simply want to stop and start them then the only requirement is that you are using a version of libcloud that supports that service (and exposes it as a public driver).

If you want to use your hosting service in conjuction with a Provisioner part you will additionally need:

 * SSH to be installed and working in the base image you choose.
 * You have credentials that can obtain root access
    * Either the service lets you set a password/SSH key at create time
    * Or the base image has credentials baked into it that you can use

