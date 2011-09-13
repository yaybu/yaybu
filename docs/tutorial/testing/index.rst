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

If you are new to Yaybu, or your configuration is still new, we strongly suggest
running in simulation mode before every deployment.

Unit Testing: Testing recipes in isolation
==========================================

You can test your recipes in a user space chroot using standard python
unittesting techniques.

Let's test something simple. Here is foo.yay::

    resources.append:
        - File:
            name: /etc/importantfile

In your test case you can write::

    from yaybu.harness import FakeChrootTestCase

    class TestMyRecipe(FakeChrootTestCase):
        def test_file_deployed(self):
            self.fixture.check_apply("""
                yay:
                  extends:
                    - foo.yay
                """)
            self.failUnlessExists("/etc/importantfile")

The fixture object provides methods for interfacing with a test environment,
in this case a user space chroot created using fakeroot, fakechroot and
cowdancer. Using sidekick, you can control multiple test VM's with the
same interface and exercise interfaces between those VM's.

.. autoclass:: yaybu.harness.Fixture
    :members:

.. autoclass:: yaybu.harness.TestCase
    :members:
    :inherited-members:

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

