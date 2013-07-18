=====
Yaybu
=====

Yaybu is a push based configuration management tool written in Python with the
goal of helping you tame your servers. You describe your infrastructure in a
simple and flexible YAML-like language and Yaybu works out what needs to happen
to deploy your updates.

We are on OFTC IRC (``irc://irc.oftc.net/yaybu``).

Here are some quick and simple Yaybu examples to show you what you can do right
now and we are working on.

The following examples go in a ``Yaybufile`` and can be executed by running
``yaybu up``.


Installing yaybu
================

An unstable 'nightly' PPA is available for lucid and precise. You can use it
like this::

    sudo add-apt-repository ppa:yaybu-team/nightly
    sudo apt-get update
    sudo apt-get install python-yaybu

(FIXME: Add details about OSX and stable debs when available).


Yaybu commands
==============

Currently the following commands are available:

up
    Apply the configuration specified in your Yaybufile
destroy
    If your configuration creates external resources like virtual machines,
    then this command will destroy it.
expand
    Print out a YAML dump of your configuration after all variables have been
    expanded and any ifs/fors/etc have been applied.
ssh
    SSH into a server using the connection details specified in your
    configuration file.

You can do ``yaybu help COMMAND`` to learn more about each of these.


Some example configurations
===========================

Deploy to an existing server or VM
----------------------------------

To deploy to your current computer by SSH you can use a ``Yaybufile`` like this::

    new Provisioner as provisioner:

        resources:

            - File:
                name: /some_empty_file

            - Execute:
                name: hello_world
                command: touch /hello_world
                creates: /hello_world

        server:
            fqdn: localhost
            username: root
            password: penguin55
            private_key: path/to/key

``fqdn`` is a fully qualified domain name (though IP addresses are also
accepted). If ``username`` isn't provided, it will use the username you are
currently logged in as. If neither ``password`` or ``private_key``, Yaybu will
consult your ssh-agent.


Deploy to AWS compute instances
-------------------------------

Provisioning of AWS instances is supported out of the box using libcloud.
You will need to have set up an SSH key in the Amazon control panel and either
have the path to the private part of that key or have added it to your
ssh-agent.

You'll need something like this in your ``Yaybufile``::

    new Provisioner as appserver:
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

    resources:
      - Package:
          name: git-core

``ex_keyname`` is the name of the SSH key pair in the amazon console.
``private_key`` is the corresponding private key.

This will create a new instance at AWS and install ``git`` on it. Running
``yaybu up`` a second time will cause yaybu to report that nothing has changed
(as yaybu is checking the existing instance for changes).


Deploy to BigV
--------------

Our BigV support is implemented via the libcloud library but is currently
residing in the Yaybu codebase. As you can set the password for an instance
when it is created there is no preparation to do to create a bigv instance,
other than creating a bigv account.

Your ``Yaybufile`` looks like this::

    new Provisioner as vm1:
        new Compute as server:
            driver:
                id: BIGV
                key: yourusername
                secret: yourpassword
                account: youraccountname

            image: precise
            name: test123456

            user: root
            password: aez5Eep4

        resources:
          - Package:
              name: git-core

This will create a new vm called ``test123456``. You will be able to log in as
root using the password ``aez5Eep4`` (though you should use pwgen to come up
with something better).


Provisioning a VMWare instance
------------------------------

You'll need a copy of VMWare Workstation, VMWare Fusion or VMWare Player.
You'll need a base image to use. My checklist when creating mine is:

 * Is ``openssh-server`` installed?
 * Is there a user with passphraseless sudo access to root?
 * Have I deleted the /etc/udev/rules.d/70-persistent-net.rules?

When you are done, shut down the VM and get the path to its VMX file.

Now your ``Yaybufile`` looks like this::

    new Provisioner as vm1:
        new Compute as server:
            driver:
                id: VMWARE
            name: mytest vm
            image:
                id: ~/vmware/ubuntu/ubuntu.vmx

            user: ubuntu

        resources:
          - Package:
              name: git-core


Provisioning multiple instances
-------------------------------

Now your ``Yaybufile`` is a bit longer and looks like this::

    new Provisioner as vm1:
        new Compute as server:
            driver:
                id: VMWARE
            name: mytest vm
            image:
                id: /home/john/vmware/ubuntu/ubuntu.vmx
            user: ubuntu

        resources:
          - File:
              name: /etc/foo
              template: sometemplate.j2
              template_args:
                  vm2_ip: {{ vm2.server.public_ips[0] }}

    new Provisioner as vm2:
        new Compute as server:
            driver:
                id: VMWARE
            name: mytestvm
            image:
                id: /home/john/vmware/ubuntu/ubuntu.vmx
            user: ubuntu

        resources:
          - File:
              name: /etc/foo
              template: sometemplate.j2
              template_args:
                  vm1_ip: {{ vm1.server.public_ips[0] }}

This configuration is interesting because vm2 references the ip address of vm1
in its configuration file and vice versa. Lazy evaluation means that
dependencies are resolved just in time, so these kinds of cyclic references
arent a show stopper.


Setting up a DNS zone on Gandi
------------------------------

This example creates a VM on bigv, installs git on it and then sets up a Gandi
DNS Zone for that VM::

    new Provisioner as vm1:
        new Compute as server:
            driver:
                id: BIGV
                key: yourusername
                secret: yourpassword
                account: youraccountname

            image: precise
            name: test123456

            user: root
            password: aez5Eep4

        resources:
          - Package:
              name: git-core

    new Zone as dns:
        driver:
            id: GANDI
            key: yourgandikey

        domain: example.com

        records:
          - name: www
            data: {{ vm1.server.public_ip }}

Obviously you can use the DNS part on its own and manually specify DNS entries.


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


Hacking on yaybu
================

To get a development environment with required dependencies::

    python bootstrap.py
    bin/buildout

Then write a configuration file called ``Yaybufile``::

And run it with::

    ./bin/yaybu up


Running the tests
-----------------

NOTE: Currently the testrunner will try and run a set of integration tests
against an ubuntu chroot. These tests are only run on ubuntu systems with the
following packages installed::

    sudo apt-get install fakechroot fakeroot debootstrap cowdancer

To run the tests you can then::

    ./bin/test

