.. Yaybu documentation master file, created by
   sphinx-quickstart on Sun Feb 13 17:37:59 2011.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Yaybu configuration management software
=======================================

Yaybu manages your deployed computer systems, in much the same was as Puppet_
or Chef_. Yaybu has many advantages over these other systems, but it is an
awful lot less mature.

Yaybu aims to provide a system that is familiar for system administrators -
they should be able to define and use complex configurations without having to
learn a programming language.

To do this Yaybu is built on top of YAY, a YAML macro language. This extends
the easy-to-use YAML language with macros for variable substitution, looping
and conditionals, that allows anyone with an understanding of a UNIX system to
write and deploy configurations easily.

Contents:

.. toctree::
   :maxdepth: 3

   intro
   terminology
   tutorial
   logging
   resources
   yay_reference
   hacking

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

