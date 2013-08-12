=====================================
Managing your cloud compute instances
=====================================

The ``Compute`` part can be used to create and destroy services in various
cloud services supported by libcloud.


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

Now we are using a Compute part as well. We have replaced the static connection
details with a part that provides them on demand. Because ``Yaybufile`` is
lazily evaluated the AWS instance isn't started until the Provisioner needs
it.

``ex_keyname`` is the name of the SSH key pair in the amazon console.
``private_key`` is the corresponding private key.

This will create a new instance at AWS and install ``git`` on it. Running
``yaybu up`` a second time will cause yaybu to report that nothing has changed
(as yaybu is checking the existing instance for changes).


Deploy to BigV
--------------

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

This is very similar to the AWS example. The two main differences are:

* Different credentials are needed to access your account (key + secret for
  AWS, where as bigv uses your username/password and an 'account').

* Different ways of setting the credentials used by the VM. AWS expects you to
  inject an SSH key via the ``ex_keyname`` field. BigV allows you to set the
  root password when you create the VM.


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
            name: mytest vm

            driver:
                id: VMWARE

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
            name: mytestvm1
            driver:
                id: VMWARE
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
            name: mytestvm2
            driver:
                id: VMWARE
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
aren't a show stopper.
