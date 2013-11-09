============
Introduction
============

The Domain Name Service
=======================

A common problem with development environments is the lack of useful DNS. Often
mistakes are made because the wrong IP addresses are used somewhere. We're
going to address this with a small DNS server called MiniDNS. This runs locally
on your computer and temporarily takes over your DNS access.  It provides a
RESTful interface that deployment software such as Yaybu can use to configure
your DNS automatically.

You can install this with::

    $ pip install minidns

Once it is installed you can run::

    $ sudo minidns start

When you do this, you’ll have a mini DNS server running on localhost. It
hijacks connections to localhost:53 and so takes over all DNS you see locally.
Yaybu will then talk to MiniDNS to tell it the names of virtual machines it
starts. This gives you tidy URLs, and means you never care about the actual IP
addresses of your virtual machines, which will save a huge amount of confusion.

Chaser
======

“Chaser” is a Django application for submitting, rating and sharing Unicorn
Chasers.  We’re going to use it as a sample application as we work through this
tutorial.  The git repository for chaser is branched, with a branch for each
part of the tutorial. 

You don’t need to know anything about Django to work with this, and you’ll
never write a line of Django code - all we’re going to do is deploy it, in
successively more interesting and more complex ways.

Connecting to our VM
====================

Yaybu provides an “ssh” command, so you can connect to machines using the same
details and credentials as Yaybu uses. You need to specify the machine just the
way you would find the provisioner in Yaybu. So for example, if you have::

    new Provisioner as foo:
    …

In your Yaybufile, you would type::

    $ yaybu ssh foo

You should specify the full yaybu path to locate the node.

To connect to our app instance therefore, you can type::

    $ yaybu ssh app

And login with the password ‘password’.

Have a look around, and you can see that Yaybu has made exactly the changes you would expect.





