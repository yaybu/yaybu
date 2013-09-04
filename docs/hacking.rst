================
Hacking on yaybu
================

If you are going to hack on Yaybu please stop by IRC and say hi! We are on OFTC
in ``#yaybu``.

The source code is available on GitHub - please fork it and send us pull requests!

The main components you might want to hack on are:

========= ================================================================
Component Description
========= ================================================================
yaybu     The main app. You'll need to change this to add new CLI subcommands or add new ``Parts``.
yay       The configuration language runtime. You will need to change this to improve parsing, the runtime graph, file transports, etc.
yaybu.app This contains a small OSX application and build scripts to package Yaybu for OSX. You will probably need to fork this to fix OSX specific bugs.



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

