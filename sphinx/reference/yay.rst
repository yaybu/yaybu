=============
YAY Reference
=============

YAY is based on YAML syntax, with extensions to provide a pythonic
macro-language over the top of YAML. This is not as mad as it sounds.

Rationale
=========

Configuration files come in a vast variety of flavours, customised for
specific needs. These vary from the very, very simple (/etc/resolv.conf for
example) to files written in Turing-complete languages (for example, Django
uses Python).

Configuration file languages have to strike a balance between two competing
goals: simplicity and power.

Simplicity
~~~~~~~~~~

On the one hand they need to be simple enough to be used by non-programmers,
and everyone benefits

Language Tour
=============

Mappings
~~~~~~~~

A mapping is a set of key value pairs. They key is a string and the value
can be any type supported by Yay. All Yay files will contain at least one
mapping::

    site-domain: www.yaybu.com
    number-of-zopes: 12
    in-production: true

You can nest them as well, as deep as you need to. Like in Python, the
relationships between each item is based on the amount of indentation::

    interfaces:
        eth0:
           interfaces: 192.168.0.1
           dhcp: yes

List
~~~~

You can create a list of things by creating an intended bulleted list::

    packages:
        - python-yay
        - python-yaybu
        - python-libvirt

If you need to express an empty list you can also do::

    packages: []

Variable Expansion
~~~~~~~~~~~~~~~~~~

If you were to specify the same Yaybu recipe over and over again you would
be able to pull out a lot of duplication. You can create templates with
placeholders in and avoid that. Lets say you were deploying into
a directory based on a customer project id::

    projectcode: MyCustomer-145

    resources:
        - Directory:
            name: /var/local/sites/${projectcode}

        - Checkout:
            name: /var/local/sites/${projectcode}/src
            repository: svn://mysvnserver/${projectcode}


Including Files
~~~~~~~~~~~~~~~

You can import a recipe using the yay extends feature. If you had a template
foo.yay::

    resources:
        - Directory:
              name: /var/local/sites/${projectcode}
        - Checkout:
              name: /var/local/sites/${projectcode}/src
              repository: svn://mysvnserver/${projectcode}

You can reuse this recipe in bar.yay like so::

    yay:
        extends:
            - foo.yay

    projectcode: MyCustomer-145


Extending Lists
~~~~~~~~~~~~~~~

If you were to speficy resources twice in the same file, or indeed across
multiple files, the most recently specified one would win::

    resources:
        - foo
        - bar

    resources:
        - baz

If you were to do this, resources would only contain baz. Yay has a function
to allow appending to predefined lists: append::

    resources:
        - foo
        - bar

    resources.append:
        - baz


For Loops
~~~~~~~~~

You might want to have a list of project codes and then define multiple
resources for each item in that list. You would do something like this::

    projectcodes:
        MyCustomer-100
        MyCustomer-72

    resources.append:
      .flatten:
        .foreach p in projectcodes:
            - Directory:
                  name: /var/local/sites/${p}
            - Checkout:
                  name: /var/local/sites/${p}/src
                  repository: svn://mysvnserver/${p}


Recipe Patterns
===============

How do i influence the order my recipes execute in?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You have a recipe where you want a resource to be inserted near the end
of the resources list, but your recipe is included too early to do that.
What can you do?

The resources list is a normal yay variable so we can exploit the variable
expansion and split your cookbooks in to phases::

    deployment: []
    finalization: []

    resources.flatten:
        - ${deployment}
        - ${finalization}

Instead of appending to resources in your recipes you'd now append to
deployment. If you need to move something to the end of execution
you can add it to the finaliztion list.
