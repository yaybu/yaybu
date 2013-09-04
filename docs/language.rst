Language Tour
=============

Yay is a non-strict language that supports lazy evaluation. It is a sort of
mutant child of YAML and Python, with some of the features of both.

There are some significant differences from YAML and this absolutely does not
attempt to implement the more esoteric parts of YAML.

A particularly significant restriction is that keys may not contain
whitespace. keys in a configuration language are expected to be simple bare
terms. This also helpfully keeps the magic smoke firmly inside our parser.

It is important to understand that for any line of input it is imperative
"pythonish" or declarative "yamlish". It actually works well and we find it
very easy to read, for example::

    a: b
    if a == 'b':
        c: d

It is pretty clear that some of those lines are declarative and some are
imperative. When in pythonish mode it works just as you would expect from
python, when in yamlish mode it works as a declarative language for defining
terms.


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
            name: /var/local/sites/{{projectcode}}

        - Checkout:
            name: /var/local/sites/{{projectcode}}/src
            repository: svn://mysvnserver/{{projectcode}}

If you variables are in mappings you can access them using ``.`` as seperator.
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

Including Files
~~~~~~~~~~~~~~~

You can import a recipe using the yay extends feature. If you had a template
``foo.yay``::

    resources:
        - Directory:
              name: /var/local/sites/{{projectcode}}
        - Checkout:
              name: /var/local/sites/{{projectcode}}/src
              repository: svn://mysvnserver/{{projectcode}}

You can reuse this recipe in ``bar.yay`` like so::

    include "foo.yay"

    include foo.bar.includes

    projectcode: MyCustomer-145


Search paths
~~~~~~~~~~~~

You can add a directory to the search path::

    search "/var/yay/includes"

    search foo.bar.searchpath

Configuration
~~~~~~~~~~~~~

::
    configure openers:
      foo: bar
        baz: quux

    configure basicauth:
        zip: zop

Ephemeral keys
~~~~~~~~~~~~~~

These will not appear in the output::

    for a in b
        set c = d.foo.bar.baz
        set d = dsds.sdsd.sewewe
        set e = as.ew.qw
        foo: c

Extending Lists
~~~~~~~~~~~~~~~

If you were to specify resources twice in the same file, or indeed across
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

    extend resources:
        - baz

Conditions
~~~~~~~~~~

::

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

For Loops
~~~~~~~~~

You might want to have a list of project codes and then define multiple
resources for each item in that list. You would do something like this::

    projectcodes:
        MyCustomer-100
        MyCustomer-72

    extend resources:

        for p in projectcodes:
            - Directory:
                  name: /var/local/sites/{{p}}

            for q in p.qcodes:
                - Checkout:
                    name: /var/local/sites/{{p}}/src
                    repository: svn://mysvnserver/{{q}}

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
                {{d}}

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
             {{f}}

That would return a list with apple and strawberry in it. The list will
be sorted alphabetically: mappings are generally unordered but we want
the iteration order to be stable.

Select
~~~~~~

The select statement is a way to have conditions in your configuration.

Lets say ``host.distro`` contains your Ubuntu version and you want to install
difference packages based on the distro. You could do something like::

    packages:
        select distro:
            karmic:
                - python-setuptools
            lucid:
                - python-distribute
                - python-zc.buildout

Function calls
~~~~~~~~~~~~~~

Any sandboxed python function can be called where an expression would exist in a yay statement::

    set foo = sum(a)
    for x in range(foo):
        - x

Class bindings
~~~~~~~~~~~~~~

Classes can be constructed on-the-fly::

    parts:
        web:
            new Compute:
                foo: bar
                % for x in range(4)
                    baz: x

Classes may have special side-effects, or provide additional data, at runtime.

Each name for a class will be looked up in a registry for a concrete implementation that is
implemented in python.

Macros
~~~~~~

Macros provided parameterised blocks that can be reused, rather like a function.

you can define a macro with::

    macro mymacro:
        foo: bar
        baz: {{thing}}

You can then call it later::

    foo:
        for q in x:
            call mymacro:
                thing: {{q}}

Prototypes
~~~~~~~~~~

Prototypes contain a default mapping which you can then override. You can
think of a prototype as a class that you can then extend.

In their final form, they behave exactly like mappings::

    prototype DjangoSite:
        set self = here

        name: www.example.com

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
            name: www.mysite.com

Here
~~~~

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
