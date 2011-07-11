============
Introduction
============

Yaybu fills the same need as Puppet_ or Chef_: it provides an automation layer
on top of your systems management processes, increasing reliability, removing
repetitive manual tasks and providing a configuration database.

.. _Puppet: http://www.puppetlabs.com/
.. _Chef: http://wiki.opscode.com/display/chef/Home

Why do CM at all
================

Are your servers a work of art? Is the only way to know which has what setup
to SSH in and look? Is it hard to review the configuration deployed on your
systems?

It looks like you haven't yet adopted configuration management.

Using configuration management techniques with the support of an automation
tool like Yaybu will:

 * Make it easier to build test environments
 * Make it easier to review configuration
 * Help to ensure consistency in your production environments


Why use Yaybu?
==============

There are a number of reasons we've written Yaybu:

 **Python**
  If you already have a significant investment in Python, as we do, you get
  a flexible automation tool that you can hack on and integrate with any
  other tools and processes you are using.
 **Awesome configuration language**
  The language used to write your configurations is where your system
  administrators will be spending a lot of their time. This language needs
  to be appropriate for their needs, with enough power that they don't
  have to cut and paste a lot of text. Yay is that language.
 **Testability**
  The biggest advantage of infrastructure as code is that you can test it.

Yaybu vs Puppet
---------------

These are things we didn't like about Puppet and inspired us to write Yaybu.

 **Explicit dependency graph**
  Deep in our hearts we love this. Its great. But it does make for more
  typing.

Yaybu vs Chef
-------------

Chef is a great piece of software, but there are some things we could
do without.

 **The Ruby DSL**
  You have to write your configuration in Ruby.

