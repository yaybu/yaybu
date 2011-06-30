==========
Quickstart
==========

Hello, World!
=============

Create a file called `helloworld.yay`::

    resources.append:
        - Execute:
            name: helloworld
            command: echo 'Hello, World!'

Then run it::

    sudo yaybu -v helloworld.yay

(It needs to run as root so it can store and retrieve state in /var/run).

You should see the following::

    /----------------------------- Execute[helloworld] -----------------------------
    | $ echo Hello, World!
    | Hello, World!
    \-------------------------------------------------------------------------------
    
    All changes were applied successfully

However, this is pretty dull.  Lets say "Hello, World!" with more panache...

Hello, World! 2
===============

Create a file called `helloworld2.yay`::

    resources.append:
        - Package:
            name: cowsay
        - Execute:
            name: helloworld
            environment:
                PATH: /bin:/usr/bin:/sbin:/usr/sbin:/usr/games
            command: cowsay 'Hello, World!'

WARNING: This configuration will install cowsay on your computer, if it's available from
your OS repositories.

Run it::

    sudo yaybu -v helloworld2.yay

You should see the following::

    /----------------------------- Execute[helloworld] -----------------------------
    | $ cowsay Hello, World!
    |  _______________
    | < Hello, World! >
    |  ---------------
    |         \   ^__^
    |          \  (oo)\_______
    |             (__)\       )\/\
    |                 ||----w |
    |                 ||     ||
    \-------------------------------------------------------------------------------
    
    All changes were applied successfully

Yaybu sanitised paths before execution, hence the need to add /usr/games
explicitly to the path here.


