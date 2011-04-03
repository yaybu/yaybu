Yaybu configuration management software
=======================================

Yaybu manages your deployed computer systems, in much the same was as Puppet_
or Chef_. Yaybu has many advantages over these other systems, but it is an
awful lot less mature.

.. _Puppet: http://www.puppetlabs.com/
.. _Chef: http://www.opscode.com/chef

Yaybu aims to provide a system that is familiar for system administrators -
they should be able to define and use complex configurations without having to
learn a programming language.

To do this Yaybu is built on top of YAY, a YAML macro language. This extends
the easy-to-use YAML language with macros for variable substitution, looping
and conditionals, that allows anyone with an understanding of a UNIX system to
write and deploy configurations easily.

Contents:

.. toctree::
   :maxdepth: 2

   intro
   installation
   terminology
   tutorial
   resources
   errorhandling
   yay_reference
   logging
   hacking
   todo

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

