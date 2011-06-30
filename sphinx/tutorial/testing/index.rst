=======
Testing
=======

If you are making minor changes, Simulation Mode can help.

However, to maintain testability of your configurations over time, you need
automated unit tests and a way of deploying configurations for integration
testing in a virtual infrastructure.  Yaybu provides all these features using
Sidekick, and test harness support within Yaybu.

Simulation Mode
===============

When you run yaybu with the `-s` switch, it will make no changes to your
system, but will print the changes that it thinks it would have to make.  Since
changes can be interdependent it can't do this with 100% reliability, but for
smaller changes this can be a very useful way of checking if a change is going
to do what you expect.

Unit Testing: Testing recipes in isolation
==========================================

.. todo:: shiny new unit tests for recipes


Integration Testing: Testing entire configurations
==================================================

.. todo:: integration testing

System Testing: Testing your final delivery
===========================================

Nagios! Write tests that continue to support your infrastructure and detect
problems in the future.  If it is something you would test after deploying a
new config, why not test it regularly and automatically?

.. toctree::
   :maxdepth: 1
   
   :doc:`sidekick <sidekick:/index>`

