=====
Yaybu
=====

Yaybu is a configuration management tool written in Python with the goal of
helping you tame your servers, and we want you to do it with a smile.

You describe your infrastructure in a simple and flexible YAML-like language
and Yaybu works out what needs to happen to deploy your updates.

We are on OFTC IRC (``irc://irc.oftc.net/yaybu``). Our docs are at
``yaybu.readthedocs.org``.


Hacking on yaybu
================

To get a development environment with required dependencies::

    python bootstrap.py
    bin/buildout

Then write a sample config file called ``foo.yay``::

    resources.append:
      - File:
          name: /some_empty_file

      - Execute:
          name: hello_world
          command: touch /hello_world
          creates: /hello_world

And run it with::

    ./bin/yaybu foo.yay


Running the tests
-----------------

NOTE: Currently the testrunner will try and run a set of integration tests
against an ubuntu chroot. Because of that we are a bit ubuntu-specific.
We'll be fixing that asap!

To run the tests::

    ./bin/test discover

