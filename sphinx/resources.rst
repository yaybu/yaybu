=========
Resources
=========

Resources are a core concept in Yaybu.

A Resource is a thing on your deployment target that can be described in
an abstract way and then be managed by Yaybu without any explicit migration
scripts being written. You define the state you want the resource to be in
and yaybu will work out how to get it there.

The management yaybu can range from something like ensure a symbolic link
exists, to applying templates to files, to making sure the right tag
of your Plone site is checked out to anything that can be expressed in
python.

You can recognise when a resource is used in a yay configuration file,
because it will be capitalised.

.. toctree::
   :maxdepth: 2

   resources/package
   resources/execute
   resources/file
   resources/directory
   resources/link
   resources/special
   resources/user
   resources/group
   resources/checkout
   resources/prompt

