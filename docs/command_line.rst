============
Command Line
============

The main command line in yaybu is ``yaybu``. If you run it with no arguments it will drop you into an interactive shell where you can run the various subcommands.

Most subcommands will need a config file. By default yaybu will search for a ``Yaybufile`` in the current directory. It will also check in parent directories. If you want to force it to use a different config file you can use the ``-c`` option::

    yaybu -c myconfig.yay test

Your configuration can declare variables that it takes on the command line. This is covered in :ref:`runtime_arguments`. If you have defined an argument called ``instance`` then you can use it with a command like this::

    yaybu up instance=test1234


``expand``
==========

Running ``yaybu expand`` evaluates your configuration without making any changes and prints to stdout a YAML or JSON representation. This is useful for checking that your loops, conditionals and variables have been evaluated as you expected by inspection.


``test``
========

The ``yaybu test`` command will run various tests on your configuration to try and find errors before you do an actual deployment. We can't guarantee success but we can:

 * Check any assets you depend on exist
 * Check your templates for errors
 * Check that any dependencies or relationships you have created between parts or resources are valid
 * Check your credentials for all the services you will be accessing


``up``
======

``yaybu up`` is the command that will actually deploy your configuration.

In order to protect your infrastructure this will automatically perform a self-test of your configuration before starting.

If you haven't defined any parts in your configuration then this command will not do anything.

This command takes ``--resume`` or ``--no-resume``. These flags control whether or not yaybu remembers trigger states between deployments. This is convered in more detail in the :ref:`Provisioner <provisioner>` section.


``destroy``
===========

When you run ``yaybu destroy`` yaybu will examine all the parts you have defined in your configuration and ask them to destroy themselves::

    $ yaybu destroy
    [*] Destroying load balancer 'test_lb'
    [*] Destroying node 'test1'
    [*] Destroying node 'test2'


``ssh``
=======

The ``yaybu ssh`` takes an expression and solves it against the configuration. For example, if you had a list of servers you could::

    yaybu ssh myservers[2]

This would start an SSH connection to the 3rd server in the list (the first server is at position 0).

If Yaybu is aware of a particular username, port, password or SSH key needed to access that server it will use it. Otherwise it will fall back to using for SSH agent.

