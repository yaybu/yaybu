=====
Yaybu
=====

.. image:: https://travis-ci.org/isotoma/yaybu.png
   :target: https://travis-ci.org/#!/isotoma/yaybu

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


Some example configurations
===========================

The following examples go in a ``Yaybufile`` and can be executed by running
``yaybu up`` (unless otherwise specified).


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

Here we are setting up a provisioner 'part'. We use the ``Yaybufile`` to plumb
together a series of parts and these parts then do the orchestration work.

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


Setting up a DNS zone on Gandi
------------------------------

This example creates a VM on bigv, installs git on it and then sets up a `Gandi
<https://www.gandi.net/>`_ DNS Zone for that VM::

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

Obviously you can use the DNS part on its own and manually specify DNS
entries::

    new Zone as dns:
        driver:
            id: GANDI
            key: yourgandikey

        domain: example.com

        records:
          - name: mail
            data: 173.194.41.86
            type: A

          - name: www
            data: www.example.org
            type: CNAME


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


The yay language
================

The language used in your ``Yaybufile`` is called ``yay``. It is YAML-like, but
has templates and pythonic expressions. Some other tools just use a templated
form of YAML, which is powerful. But not as powerful as when these new features
are first class citizens of the language.

In this section we'll skim through some of the important bits.

If you like it, it is packaged as a separate library and can be used in your
own python applications.


Variables
---------

You can refer to any structure through the variable syntax::

    me:
      name: John
      nick: Jc2k

    message: Hello, {{ me.nick }}!


Lazy evaluation
---------------

Yay is a non-strict, lazyily evaluated language. This means that expressions are
calculated when they are required not when they are declared::

    var1: 50
    var2: {{ var1 + 5 }}
    var1: 0

In an imperative language ``var2`` would be ``55``. But it is actually ``5``.
Stated like this it seems weird and counterintuitive. So lets see how it is
useful. Imagine you have a firewall recipe saved as ``firewall.yay``::

    firewall:
       allow_pings: true
       open:
         - range: 1.1.1.1/32

    resources:
      - File:
          name: /etc/iptables.conf
          template: iptables.conf.j2
          template_args:
              rules: {{ firewall }}

Now for a contrived reason approved in a secret court your new projects server
can't be pingable. You can't just use your existing ``firewall.yay``... Wait,
you can. In your ``Yaybufile``::

    include "firewall.yay"

    firewall:
        allow_pings: false


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

File
~~~~

A provider for this resource will create or amend an existing file to the
provided specification.

For example, the following will create the /etc/hosts file based on a static
local file::

    extend resources:
      - File:
          name: /etc/hosts
          owner: root
          group: root
          mode: 644
          static: my_hosts_file

The following will create a file using a jinja2 template, and will back up the
old version of the file if necessary::

    extend resources:
      - File:
          name: /etc/email_addresses
          owner: root
          group: root
          mode: 644
          template: email_addresses.j2
          template_args:
             foo: foo@example.com
             bar: bar@example.com
          backup: /etc/email_addresses.{year}-{month}-{day}

The available parameters are:

``name``
    The full path to the file this resource represents.
``owner``
    A unix username or UID who will own created objects. An owner that
    begins with a digit will be interpreted as a UID, otherwise it will be
    looked up using the python 'pwd' module.
``group``
    A unix group or GID who will own created objects. A group that begins
    with a digit will be interpreted as a GID, otherwise it will be looked up
    using the python 'grp' module.
``mode``
    A mode representation as an octal. This can begin with leading zeros if
    you like, but this is not required. DO NOT use yaml Octal representation
    (0o666), this will NOT work.
``static``
    A static file to copy into this resource. The file is located on the
    yaybu path, so can be colocated with your recipes.
``template``
    A jinja2 template, used to generate the contents of this resource. The
    template is located on the yaybu path, so can be colocated with your
    recipes
``template_args``
    The arguments passed to the template.


Directory
~~~~~~~~~

A directory on disk. Directories have limited metadata, so this resource is
quite limited.

For example::

    extend resources:
      - Directory:
          name: /var/local/data
          owner: root
          group: root
          mode: 0755

The available parameters are:

``name``
    The full path to the directory on disk
``owner``
    The unix username who should own this directory, by default this is 'root'
``group``
    The unix group who should own this directory, by default this is 'root'
``mode``
    The octal mode that represents this directory's permissions, by default
    this is '755'.
``parents``
    Create parent directories as needed, using the same ownership and
    permissions, this is False by default.


Link
~~~~

A resource representing a symbolic link. The link will be from `name` to `to`.
If you specify owner, group and/or mode then these settings will be applied to
the link itself, not to the object linked to.

For example::

    extend resources:
      - Link:
          name: /etc/init.d/exampled
          to: /usr/local/example/sbin/exampled
          owner: root
          group: root

The available parameters are:

``name``
    The name of the file this resource represents.
``owner``
    A unix username or UID who will own created objects. An owner that
    begins with a digit will be interpreted as a UID, otherwise it will be
    looked up using the python 'pwd' module.
``group``
    A unix group or GID who will own created objects. A group that begins
    with a digit will be interpreted as a GID, otherwise it will be looked up
    using the python 'grp' module.
``to``
    The pathname to which to link the symlink. Dangling symlinks ARE
    considered errors in Yaybu.


Execute
~~~~~~~

Execute a command. This command *is* executed in a shell subprocess.

For example::

    extend resources:
      - Execute:
          name: core_packages_apt_key
          command: apt-key adv --keyserver keyserver.ubuntu.com --recv-keys {{source.key}}

A much more complex example. This shows executing a command if a checkout
synchronises::

    extend resources:
      for bi in flavour.base_images:
        - Execute:
            name: base-image-{{bi}}
            policy:
              apply:
                  when: sync
                  on: /var/local/checkouts/ci
            command: ./vmbuilder-{{bi}}
            cwd: /var/local/checkouts/ci
            user: root

The available parameters are:

``name``
    The name of this resource. This should be unique and descriptive, and
    is used so that resources can reference each other.
``command``
    If you wish to run a single command, then this is the command.
``commands``
    If you wish to run multiple commands, provide a list
``cwd``
    The current working directory in which to execute the command.
``environment``
    The environment to provide to the command, for example::

        extend resources:
          - Execute:
              name: example
              command: echo $FOO
              environment:
                  FOO: bar

``returncode``
    The expected return code from the command, defaulting to 0. If the
    command does not return this return code then the resource is considered
    to be in error.
``user``
    The user to execute the command as.
``group``
    The group to execute the command as.
``umask``
    The umask to use when executing this command
``unless``
    A command to run to determine is this execute should be actioned
``creates``
    The full path to a file that execution of this command creates. This
    is used like a "touch test" in a Makefile. If this file exists then the
    execute command will NOT be executed.
``touch``
    The full path to a file that yaybu will touch once this command has
    completed successfully. This is used like a "touch test" in a Makefile. If
    this file exists then the execute command will NOT be executed.


Checkout
~~~~~~~~

This represents a "working copy" from a Source Code Management system.
This could be provided by, for example, Subversion or Git remote
repositories.

Note that this is '*a* checkout', not 'to checkout'. This represents the
resource itself on disk. If you change the details of the working copy
(for example changing the branch) the provider will execute appropriate
commands (such as ``svn switch``) to take the resource to the desired state.

For example::

    extend resources:
      - Checkout:
          name: /usr/src/myapp
          repository: https://github.com/myusername/myapp
          scm: git

The available parameters are:

``name``
    The full path to the working copy on disk.
``repository``
    The identifier for the repository - this could be an http url for
    subversion or a git url for git, for example.
``branch``
    The name of a branch to check out, if required.
``tag``
    The name of a tag to check out, if required.
``revision``
    The revision to check out or move to.
``scm``
    The source control management system to use, e.g. subversion, git.
``scm_username``
    The username for the remote repository
``scm_password``
    The password for the remote repository.
``user``
    The user to perform actions as, and who will own the resulting files.
    The default is root.
``group``
    The group to perform actions as. The default is to use the primary group of
    ``user``.
``mode``
    A mode representation as an octal. This can begin with leading zeros if
    you like, but this is not required. DO NOT use yaml Octal representation
    (0o666), this will NOT work.


Package
~~~~~~~

Represents an operating system package, installed and managed via the
OS package management system. For example, to ensure these three packages
are installed::

    extend resources:
      - Package:
          name: apache2

The available parameters are:

``name``
    The name of the package. This can be a single package or a list can be
    supplied.
``version``
    The version of the package, if only a single package is specified and
    the appropriate provider supports it (the Apt provider does not support
    it).
``purge``
    When removing a package, whether to purge it or not.


User
~~~~

A resource representing a UNIX user in the password database. The underlying
implementation currently uses the "useradd" and "usermod" commands to implement
this resource.

This resource can be used to create, change or delete UNIX users.

For example::

    extend resources:
      - User:
          name: django
          fullname: Django Software Owner
          home: /var/local/django
          system: true
          disabled-password: true

The available parameters are:

``name``
    The username this resource represents.
``password``
    The encrypted password, as returned by crypt(3). You should make sure
    this password respects the system's password policy.
``fullname``
    The comment field for the password file - generally used for the user's
    full name.
``home``
    The full path to the user's home directory.
``uid``
    The user identifier for the user. This must be a non-negative integer.
``gid``
    The group identifier for the user. This must be a non-negative integer.
``group``
    The primary group for the user, if you wish to specify it by name.
``groups``
    A list of supplementary groups that the user should be a member of.
``append``
    A boolean that sets how to apply the groups a user is in. If true then
    yaybu will add the user to groups as needed but will not remove a user from
    a group. If false then yaybu will replace all groups the user is a member
    of. Thus if a process outside of yaybu adds you to a group, the next
    deployment would remove you again.
``system``
    A boolean representing whether this user is a system user or not. This only
    takes effect on creation - a user cannot be changed into a system user once
    created without deleting and recreating the user.
``shell``
    The full path to the shell to use.
``disabled_password``
    A boolean for whether the password is locked for this account.
``disabled_login``
    A boolean for whether this entire account is locked or not.


Group
~~~~~

A resource representing a unix group stored in the /etc/group file.
``groupadd`` and ``groupmod`` are used to actually make modifications.

For example::

    extend resources:
      - Group:
          name: zope
          system: true

The available parameters are:

``name``
    The name of the unix group.
``gid``
    The group ID associated with the group. If this is not specified one will
    be chosen.
``system``
    Whether or not this is a system group - i.e. the new group id will be
    taken from the system group id list.
``password``
    The password for the group, if required


Service
~~~~~~~

This represents service startup and shutdown via an init daemon.

The available parameters are:

``name``
    A unique name representing an initd service. This would normally match the
    name as it appears in /etc/init.d.
``priority``
    Priority of the service within the boot order. This attribute will have no
    effect when using a dependency or event based init.d subsystem like upstart
    or systemd.
``start``
    A command that when executed will start the service. If not provided, the
    provider will use the default service start invocation for the init.d
    system in use.
``stop``
    A command that when executed will start the service. If not provided, the
    provider will use the default service stop invocation for the init.d system
    in use.
``restart``
    A command that when executed will restart the service. If not provided, the
    provider will use the default service restart invocation for the init.d
    system in use. If it is not possible to automatically determine if the restart
    script is avilable the service will be stopped and started instead.
``reconfig``
    A command that when executed will make the service reload its
    configuration file.
``running``
    A comamnd to execute to determine if a service is running. Should have an
    exit code of 0 for success.
``pidfile``
    Where the service creates its pid file. This can be provided instead of
    ``running``  as an alternative way of checking if a service is running or not.


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

