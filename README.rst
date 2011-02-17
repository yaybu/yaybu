
Hacking on yaybu
================

To get a development environment with required dependencies::

    virtualenv venv
    source venv/bin/activate
    python bootstrap.py
    bin/buildout

Running the tests
-----------------

You first need to build a fake environment in which to run the tests::

    ./bin/build-environment

To run the tests::

    ./bin/test discover

Further documentation
=====================

See html/ for the documentation in html format.

The restructured text to generate this markup is in sphinx/

