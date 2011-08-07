==========
Quickstart
==========

This quickstart tutorial assumes that you're using an operating system with apt installed
and configured, and with the 'hello' and 'cowsay' packages available from your OS
repositories.

Hello, World!
=============

.. warning::
    This tutorial will install the 'hello' and 'cowsay' packages on any compatible system
    that it is run on.

Create a file called `myconfig.yay`::

    resources.append:
        - Package:
            name: hello

Now let's apply this configuration to your system::

    sudo yaybu myconfig.yay

.. note::
    Yaybu must always be run as root so that it can store and retrieve state in /var/run.

You should see the following::

    /------------------------------- Package[hello] --------------------------------
    | # apt-get install -q -y hello
    | Reading package lists...
    | Building dependency tree...
    | Reading state information...
    | 
    | The following NEW packages will be installed:
    |   hello
    | 0 upgraded, 1 newly installed, 0 to remove and 60 not upgraded.
    | Need to get 0 B/62.4 kB of archives.
    | After this operation, 668 kB of additional disk space will be used.
    | Selecting previously deselected package hello.
    | (Reading database ... 100%
    | (Reading database ... 147192 files and directories currently installed.)
    | Unpacking hello (from .../archives/hello_2.7-1_amd64.deb) ...
    | Processing triggers for install-info ...
    | Processing triggers for man-db ...
    | Setting up hello (2.7-1) ...
    \-------------------------------------------------------------------------------

    All changes were applied successfully

Hello, Resources!
=================

A Yaybu configuration describes a `state` that you wish your system to be in, where the
`state` is described by a list of `resources`. Resources are the building blocks of any
yaybu configuration, In `myconfig.yay`, we used a `Package` resource, passing it the
argument "name: hello".

A simple, hypothetical, website server configuration might require that:

    * A restricted user account is present on the system for executing the site's code
    * Four directories are present, for:
        * the source code
        * the website executables
        * the media
        * the site logs
    * The latest version of some source code is present on the system
    * A database migration script is executed if the source code is updated

So we'd require a User resource, four Directory resources, a Checkout resource (used to
check out source code), and an Execute resource, respectively. Simple! There are more
resources that you can use, and their configuration options are described in the `resource
reference <../reference/resources>`_.

Hello, Idempotance!
===================

Our config file `myconfig.yay` describes a `state` we want our system to be in. So, what
happens if we run::

    sudo yaybu myconfig.yay

for a second time? Well, since the system is already in the state described by our
configuration, Yaybu produces the following output::

    No changes were required

Any configurations we produce should always be
`idempotant <http://wikipedia.org/wiki/Idempotence>`_, meaning that if Yaybu applies a
configuration multiple times to a system, Yaybu will only apply the parts of the
configuration that aren't consistent with the state of the system. If the system and
configuration remain the same, after the initial application of the configuration, Yaybu
will not need to do anything.

Now, let's add another `Package` resource, to install cowsay, altering myconfig.yay to
look as follows::

    resources.append:
        - Package:
            name: hello

        - Package:
            name: cowsay

Then run Yaybu::

    sudo yaybu myconfig.yay

producing the following output::

    /------------------------------- Package[cowsay] -------------------------------
    | # apt-get install -q -y cowsay
    | Reading package lists...
    | Building dependency tree...
    | Reading state information...
    | 
    | Suggested packages:
    |   filters
    | The following NEW packages will be installed:
    |   cowsay
    | 0 upgraded, 1 newly installed, 0 to remove and 83 not upgraded.
    | Need to get 0 B/20.8 kB of archives.
    | After this operation, 287 kB of additional disk space will be used.
    | Selecting previously deselected package cowsay.
    | (Reading database ... 100%
    | (Reading database ... 148366 files and directories currently installed.)
    | Unpacking cowsay (from .../cowsay_3.03+dfsg1-3_all.deb) ...
    | Processing triggers for man-db ...
    | Setting up cowsay (3.03+dfsg1-3) ...
    \-------------------------------------------------------------------------------

    All changes were applied successfully

So this time, when applying our configuration, Yaybu has found that only the cowsay
package needs to be installed, since the hello package is already installed.

Hello, Yaybu Remote!
====================

.. warning::
    Yaybu and ssh must be installed on the remote computer.

Finally, we will deploy a configuration stored on our local machine to another computer.

Let's take a new configuration `myconfig2.yay` in which we:

    * Ensure that there is a directory called `checkouts` in /tmp to checkout code into
    * Clone a particular branch of a git repository into it

::

    resources.append:
        - Directory:
            name: /tmp/checkouts
            mode: 655

        - Checkout:
            name: /tmp/checkouts/yaybu-examples
            scm: git
            repository: git://github.com/isotoma/yaybu-examples.git
            branch: master

To apply this configuration to a remote system, we need only run the following command::

    yaybu --host=foo@example.com myconfig2.yay

Where we assume that the user 'foo' will have superuser permissions and ssh access on the
remote system.

Once the user has authenticated with the host specified, Yaybu will be run remotely, and
will pass all of its output back to your local machine via the encrypted ssh connection,
as follows::

   /-------------------------- Directory[/tmp/checkouts] --------------------------
   | # /bin/mkdir /tmp/checkouts
   | # /bin/chmod 655 /tmp/checkouts
   \-------------------------------------------------------------------------------

   /------------------- Checkout[/tmp/checkouts/yaybu-examples] -------------------
   | # /bin/mkdir /tmp/checkouts/yaybu-examples
   | # git --no-pager init /tmp/checkouts/yaybu-examples
   | Initialized empty Git repository in /tmp/checkouts/yaybu-examples/.git/
   | # git --no-pager remote add origin git://github.com/isotoma/yaybu-examples.git
   | # git --no-pager fetch origin
   | From git://github.com/isotoma/yaybu-examples
   |  * [new branch]      master     -> origin/master
   | fatal: Needed a single revision
   | # git --no-pager checkout remotes/origin/master
   | Note: checking out 'remotes/origin/master'.
   | 
   | You are in 'detached HEAD' state. You can look around, make experimental
   | changes and commit them, and you can discard any commits you make in this
   | state without impacting any branches by performing another checkout.
   | 
   | If you want to create a new branch to retain commits you create, you may
   | do so (now or later) by using -b with the checkout command again. Example:
   | 
   |   git checkout -b new_branch_name
   | 
   | HEAD is now at 7d9c635... Add .gitignore and fix sphinx config
   \-------------------------------------------------------------------------------

   All changes were applied successfully

The folder was created and the code was checked out. 

.. note::
    If the code on the master branch of the yaybu-examples repository was updated, then
    afterwards we ran Yaybu with our myconfig2.yay config again, Yaybu would update the
    code to the new state of the master branch.
