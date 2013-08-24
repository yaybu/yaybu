==================
Language reference
==================

The language used in your ``Yaybufile`` is called ``yay``. It is YAML-like, but
has templates and pythonic expressions. Some other tools just use a templated
form of YAML, which is powerful. But not as powerful as when these new features
are first class citizens of the language.

In this section we'll skim through some of the important bits.

If you like it, it is packaged as a separate library and can be used in your
own python applications.


Mappings
========

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
====

You can create an ordered list of things by creating an intended bulleted
list::

    packages:
        - python-yay
        - python-yaybu
        - python-libvirt

If you need to express an empty list you can also do::

    packages: []

If a list is already defined and you wish to extend from elsewhere in your configuration you can use the ``extend`` keyword::

    extend packages:
        - python-libcloud


Variables
=========

If you were to specify the same Yaybu recipe over and over again you would
be able to pull out a lot of duplication. You can create templates with
placeholders in and avoid that. Lets say you were deploying into
a directory based on a customer project id::

    projectcode: MyCustomer-145

    resources:
        - Directory:
            name: /var/local/sites/{{projectcode}}

        - Checkout:
            name: /var/local/sites/{{projectcode}}/src
            repository: svn://mysvnserver/{{projectcode}}

If your variables are in mappings you can access them using ``.`` as separator.
You can also access specific items in lists with ``[]``::

    projects:
      - name: www.foo.com
        projectcode: Foo-1
        checkout:
            repository: http://github.com/isotoma/foo
            branch: master

    resources:
        - Checkout:
            repository: /var/local/sites/{{projects[0].checkout.repository}}

Sometimes you might only want to optionally set variables in your
configuration. Here we pickup ``project.id`` if its set, but fall back
to ``project.name``::

    project:
        name: www.baz.com

    example_key: {{project.id else project.name}}


Lazy evaluation
===============

Yay is a non-strict, lazyily evaluated language. This means that expressions are
calculated when they are required not when they are declared::

    var1: 50
    var2: {{ var1 + 5 }}
    var1: 0

In an imperative language ``var2`` would be ``55``. But it is actually ``5``.
Stated like this it seems weird and counterintuitive. So lets see how it is
useful. Imagine you have a firewall recipe saved as ``firewall.yay``::

    firewall:
       allow_pings: true
       open:
         - range: 1.1.1.1/32

    resources:
      - File:
          name: /etc/iptables.conf
          template: iptables.conf.j2
          template_args:
              rules: {{ firewall }}

Now for a contrived reason approved in a secret court your new projects server
can't be pingable. You can't just use your existing ``firewall.yay``... Wait,
you can. In your ``Yaybufile``::

    include "firewall.yay"

    firewall:
        allow_pings: false


Including Files
===============

You can reuse configuration fragments by saving them as a ``.yay`` file and using the ``include`` keyword. If you had a ``foo.yay`` that looked like this::

    resources:
        - Directory:
              name: /var/local/sites/{{projectcode}}
        - Checkout:
              name: /var/local/sites/{{projectcode}}/src
              repository: svn://mysvnserver/{{projectcode}}

You could reuse this recipe in your ``Yaybufile`` like so::

    include "foo.yay"

    projectcode: MyCustomer-145

You can control where Yaybu looks for include files by manipulating the ``searchpath``::

    yaybu:
        extend searchpath:
            - path/to/yay/files


Ephemeral metadata and variables
================================

Ephemeral variables do not appear in the final configuration. They are scratch space that enable DRY practice.

They are especially useful in for-loops::

    extend resources:
        for site in all_sites:
            set directory = "/var/www/" + site.name

            - Directory:
                  name: {{ directory }}

            - File:
                  name: {{ directory }}/mytemplate.cfg
                  static: mytemplate.cfg


Conditional expressions
=======================

One way to have conditions in your configuration file is with the ``if`` keyword::

    foo:
        if averylongvariablename == anotherverylongvariablename and \
            yetanothervariable == d and e == f:

          bar:
            quux:
                foo:
                    bar: baz

        elif blah == something:
            moo: mah

        else:
          - baz

The select statement is another way to have conditions in your configuration.

Lets say ``host.distro`` contains your Ubuntu version and you want to install
difference packages based on the distro. You could do something like::

    packages:
        select host.distro:
            karmic:
                - python-setuptools
            lucid:
                - python-distribute
                - python-zc.buildout


For Loops
=========

You might want to have a list of project codes and then define multiple
resources for each item in that list. You would do something like this::

    projects:
        - name: MyCustomer-100
          checkouts:
            - https://svn.example.com/svn/example1

        - name: MyCustomer-72
          checkouts:
            - https://svn.example.com/svn/example1
            - https://svn.example.com/svn/example2

    extend resources:
        for p in projects:
            - Directory:
                  name: /var/local/sites/{{ p }}

            for c in p.checkouts:
                - Checkout:
                    name: /var/local/sites/{{ p }}/src/{{ c }}
                    repository: svn://mysvnserver/{{ c }}

You can also have conditions::

    fruit:
        - name: apple
          price: 5
        - name: lime
          price: 10

    cheap:
        for f in fruit if f.price < 10:
            - {{f}}


You might need to loop over a list within a list::

    staff:
      - name: Joe
        devices:
          - macbook
          - iphone

      - name: John
        devices:
          - air
          - iphone

    stuff:
        for s in staff:
            for d in s.devices:
                - {{d}}

This will produce a single list that is equivalent to::

    stuff:
      - macbook
      - iphone
      - air
      - iphone

You can use a for against a mapping too - you will iterate over its
keys. A for over a mapping with a condition might look like this::

    fruit:
      # recognised as decimal integers since they look a bit like them
      apple: 5
      lime: 10
      strawberry: 1

    cheap:
        for f in fruit:
           if fruit[f] < 10:
              - {{f}}

That would return a list with apple and strawberry in it. The list will
be sorted alphabetically: mappings are generally unordered but we want
the iteration order to be stable.


Function calls
==============

Any sandboxed python function can be called where an expression would exist in a yay statement::

    set foo = sum(a)
    for x in range(foo):
        - x


Here
====

Here is a reserved word that expands to the nearest parent node that is a mapping.

You can use it to refer to siblings::

    some_data:
        sitename: www.example.com
        sitedir: /var/www/{{ here.sitename }}

You can use it with ``set`` to refer to specific points of the graph::

     some_data:
         set self = here

        nested:
            something: goodbye
            mapping: {{ self.something }}         # Should be 'hello'
            other_mapping: {{ here.something }}   # Should be 'goodbye'

        something: hello


Macros and Prototypes
=====================

Macros provided parameterised blocks that can be reused.

you can define a macro with::

    macro mymacro:
        foo: bar
        baz: {{thing}}

You can then call it later::

    foo:
        for q in x:
            call mymacro:
                thing: {{q}}

Prototypes contain a default mapping which you can then override. They
are different from macros in that a prototype is not parameterised, but
can instead be extended.

In their final form, they behave exactly like mappings::

    prototype DjangoSite:
        set self = here

        name: www.example-site.com

        sitedir: /var/local/sites/{{ self.name }}
        rundir: /var/run/{{ self.name }}
        tmpdir: /var/tmp/{{ self.name }}

        resources:
            - Directory:
                name: {{ self.tmpdir }}

            - Checkout:
                name: {{ self.sitedir}}
                source: git://github.com/

    some_key:
        new DjangoSite:
            sitename: www.example.com

