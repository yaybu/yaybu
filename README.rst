==============================
Yaybu Configuration Management
==============================

Yaybu provides a simple configuration format for describing your infrastructure,
and tools to turn that configuration into a running server.


Hacking on yaybu
================

To get a development environment with required dependencies::

    virtualenv venv
    source venv/bin/activate
    python bootstrap.py
    bin/buildout

(The virtualenv is not strictly required).

Running the tests
-----------------

NOTE: Currently the testrunner will try and run a set of integration tests
against an ubuntu chroot. Because of that we are a bit ubuntu-specific.
We'll be fixing that asap!

You first need to build a fake environment in which to run the tests::

    ./bin/build-environment

To run the tests::

    ./bin/test discover

Further documentation
=====================

See html/ for the documentation in html format.

The restructured text to generate this markup is in sphinx/

