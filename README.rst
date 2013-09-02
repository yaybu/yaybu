=====
Yaybu
=====

.. image:: https://travis-ci.org/yaybu/yaybu.png?branch=master
   :target: https://travis-ci.org/#!/yaybu/yaybu

Yaybu is a push based configuration management tool written in Python with the
goal of helping you tame your servers. You describe your infrastructure in a
simple and flexible YAML-like language and Yaybu works out what needs to happen
to deploy your updates.

Here are some quick and simple Yaybu examples to show you what you can do right
now and we are working on.


Installing yaybu
================

An unstable 'nightly' PPA is available for lucid and precise. You can use it
like this::

    sudo add-apt-repository ppa:yaybu-team/nightly
    sudo apt-get update
    sudo apt-get install python-yaybu

(FIXME: Add details about OSX and stable debs when available).


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
                id: EC2
                key: yourusername
                secret: yourpassword

            image: ami-57afb223
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



EXPERIMENTAL: Provisioning on commit (via Travis CI)
----------------------------------------------------

Travis CI has a mechansim to encrypt secrets. It also has a hook that is run on
success. This means we can have yaybu perform system orchestration tasks on
commit + successful CI run without having to run any of our own servers.

Here is a simple ``Yaybufile``::

    yaybu:
        options:
            - name: BIGV_KEY
            - name: BIGV_SECRET
            - name: BIGV_ACCOUNT
            - name: BIGV_ROOT_PASSWORD
              default: penguin55

    new Provisioner as myexample:
        new Compute as server:
            driver:
                id: BIGV
                key: {{ yaybu.argv.BIGV_KEY }}
                secret: {{ yaybu.argv.BIGV_SECRET }}

            image: precise

            name: myexample

            user: root
            password: {{ yaybu.argv.BIGV_ROOT_PASSWORD }}

        resources:
          - Package:
              name: git-core

          - Checkout:
             name: /tmp/yaybu
             scm: git
             repository: https://github.com/yaybu/example

The ``yaybu.options`` section allows us to define arguments that can be passed
to yaybu via the command line. You can define defaults to use if no such
argument is passed in.

Now we can encrypt these details using the travis command line tool::

    travis encrypt BIGV_KEY=myusername --add env.global
    travis encrypt BIGV_SECRET=password --add env.global
    travis encrypt BIGV_ACCOUNT=myaccount --add env.global
    travis encrypt BIGV_ROOT_PASSWORD=password --add env.global

And here is what your ``.travis.yml`` looks like::

    language: python
    pythons:
      - "2.6"

    env:
      global:
        - secure: <YOUR_ENCRYPTED_STRINGS>

    script:
      - true # This is where you would normally run your tests

    after_success:
      - sudo add-apt-repository yaybu-team/yaybu
      - sudo apt-get update
      - sudo apt-get install python-yaybu
      - yaybu up BIGV_KEY=$BIGV_KEY BIGV_SECRET=$BIGV_SECRET BIGV_ACCOUNT=$BIGV_ACCOUNT BIGV_ROOT_PASSWORD=$BIGV_ROOT_PASSWORD


EXPERIMENTAL: Provisioning on commit
------------------------------------

This uses a new command, ``yaybu run``. This puts yaybu into a mode where it
continues to run, rather than deploying then exiting. Parts can set up
listeners to respond to external events like commits or monitoring systems.

To deploy on commit you can use a ``Yaybufile`` like this::


    new GitChangeSource as changesource:
        polling-interval: 10
        repository: https://github.com/isotoma/yaybu

    new Provisioner as myexample:
        new Compute as server:
            driver:
                id: EC2_EU_WEST
                key: mykey
                secret: mysecret

            size: t1.micro
            image: ami-4f504f3b

            ex_keyname: mysshkey
            name: myexample

            user: ubuntu
            private_key: mysshkey.pem

        resources:
          - Package:
              name: git-core

          - Checkout:
             name: /tmp/yaybu
             scm: git
             repository: {{ changesource.repository }}
             revision: {{ changesource.master }}


The ``GitChangeSource`` part polls and sets ``{{changesource.master}}`` with
the SHA of the current commit.

This example changesource polls to learn if a new commit has occurred. This is
only because the part is an example implementation - it could easily be a
webhook or zeromq push event.

The ``Checkout`` resource uses the ``master`` property of ``changesource``.
Yaybu can use this dependency information to know that the ``Provisioner`` that
owns the ``Checkout`` is stale and needs applying every time ``master``
changes.

If your Yaybufile contained another ``Provisioner`` that didn't have such a
``Checkout`` (perhaps its the database server) then Yaybu would equally know
*not* to deploy to it on commit.


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
            username: root
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

For vim users, `vim-gnupg <https://github.com/jamessan/vim-gnupg>`_ is a gret
way to transparently edit your GPG armored configuration files.


Hacking on yaybu
================

If you are going to hack on Yaybu please stop by IRC and say hi! We are on OFTC
in ``#yaybu``.

To get a development environment with required dependencies::

    virtualenv .
    ./bin/pip install -r requirements.txt

NOTE: Currently the testrunner will try and run a set of integration tests
against an ubuntu chroot. These tests are only run on ubuntu systems with the
following packages installed::

    sudo apt-get install fakechroot fakeroot debootstrap cowdancer

To run the test::

    ./bin/nose2

Then write a configuration file called ``Yaybufile``::

And run it with::

    ./bin/yaybu up

