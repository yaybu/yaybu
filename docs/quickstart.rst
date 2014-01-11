==========
Quickstart
==========

Here are some quick and simple Yaybu examples to show you what you can do right
now and we are working on.

Yaybufile
=========

To use Yaybu you write first need to write a ``Yaybufile``. This describes the
infrastructure you want to deploy.

Here is an example that provisions 2 compute nodes with different hosting
providers and sets up subdomains for them. Yaybu is quite happy talking to
Amazon EC2, BigV and Gandi DNS all from the same deployment::

    new Provisioner as instance1:
        new Compute as server:
            driver:
                id: BIGV
                key: yourusername
                secret: yourpassword
                account: youraccountname

            image: precise
            name: test_at_bigv

            user: root
            password: aez5Eep4

        resources:
          - File:
              name: /etc/heartbeat.conf
              template: heartbeat.conf.j2
              template_args:
                  partner: {{ instance2.public_ip }}

    new Provisioner as instance2:
        new Compute as server:
            driver:
                id: EC2_EU
                key: yourusername
                secret: yourpassword

            image: ami-000cea77
            size: t1.micro
            name: test_at_ec2

            user: root
            public_key: instance2.pub
            private_key: instance2.priv

        resources:
          - File:
              name: /etc/heartbeat.conf
              template: heartbeat.conf.j2
              template_args:
                  partner: {{ instance1.public_ip }}

    new Zone as dns:
        driver:
            id: GANDI
            key: yourgandikey

        domain: example.com

        records:
          - name: instance1
            data: {{ instance1.server.public_ip }}
          - name: instance2
            data: {{ instance2.server.public_ip }}


Yaybu commands
==============

Currently the following commands are available:

``yaybu up``
    Apply the configuration specified in your Yaybufile
``yaybu destroy``
    If your configuration creates external resources like virtual machines,
    then this command will destroy it.
``yaybu expand``
    Print out a YAML dump of your configuration after all variables have been
    expanded and any ifs/fors/etc have been applied.
``yaybu ssh``
    SSH into a server using the connection details specified in your
    configuration file.

You can do ``yaybu help COMMAND`` to learn more about each of these.


Yaybu parts
===========

Parts are the building blocks that you connect together to describe your
services and how to deploy them. There are several core ones at the moment.

Compute
-------

The ``Compute`` part can be used to create and destroy services in various
cloud services supported by libcloud.

Provisioner
-----------

The ``Provisioner`` part provides idempotent configuration of UNIX servers that
can be accessed by SSH. It can be connected to ``Compute`` part to create and
deploy to a new cloud server, or it can be pointed at a static set of SSH
connection details to deploy to a dedicated server.

The part needs connection details, these are provided through the ``server``
parameter::

    new Provisioner as provisioner:
        server:
            fqdn: example.com
            port: 22
            user: root
            password: penguin55
            private_key: path/to/id_rsa

The part deploys a list of resources provided by the ``resources`` parameter.
These are idempotent - when used correctly they only make changes that need
making, which means that you can see quite clearly what has been changed by an
update deployment and it is safe to run repeatedly.

For detailed documentation of the resources you can you see the
`online documention <https://yaybu.readthedocs.org/en/latest/provisioner.html#built-in-resources>`_.

Zone
----

The ``Zone`` part uses the libcloud DNS API to manage DNS entries in various
cloud services.


Keeping secrets secret
======================

You can reference encrypted yay files in your ``Yaybufile``::

    include "mysecrets.yay.gpg"

Any include of a ``.gpg`` file is automatically decrypted, using your
``gpg-agent`` to prompt for any passphrases that are required.

Additionally the file ``~/.yaybu/defaults.yay.gpg`` is automatically loaded
when Yaybu starts. This is useful for storing your credentials/tokens outside
of your code repository and easily injected them into multiple projects.

For vim users, `vim-gnupg <https://github.com/jamessan/vim-gnupg>`_ is a great
way to transparently edit your GPG armored configuration files.

