Tutorial
========

Simple PHP Host
---------------

We have a computer "mybox" on which we wish to deploy a simple PHP application
from Subversion, based on tagged versions of the php content: i.e. we tag our
trunk each time we wish to release a new version, as good boys do.

We'll use yay to make several reusable parts, starting at a simple recipe that
just installs packages and working up to having a `mybox.yay` that just has a
list of sites to deploy.

This is meant to introduce you to the core concepts of yaybu and yay. It is
NOT a production ready recipe for Apache and PHP on Linux!!


Your first recipe: installing some packages
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

We'll meet our first resource type and how to get them to apply.

In `mybox.yay` add the following::

    resources.append:
        - Package:
            - name: openssh-server
            - name: apache2
            - name: libapache2-mod-php5

You can deploy this on the current machine with::

    sudo yaybu `mybox.yay`

The goal of all your recipes is to add resource objects to the `resources` list.
Resources always start with a capital letter and describe things on a server
that you want to manage. They are meant to be declarative: They describe
the state you want to achieve.

There are 2 forms you can use when appending to the resource list. The first
is::

    resources.append:
        - Package:
            name: openssh-server
        - Package:
            name: apache2

This adds 2 Package resources to the list, and while readable can get verbose.
So you can also::

    resources.append:
        - Package:
            - name: openssh-server
            - name: apache2

Which will have the same result.


Enabling Apache Modules
~~~~~~~~~~~~~~~~~~~~~~~

We'll meet some new resource types and how to reuse yaybu recipes.

Lets add a new file. In apache_modules.yay add::

    modules: []

    resources.append:
        .foreach module in modules:
            Execute:
              name: enable-${module}
              command: a2enmod ${module}
              creates: /etc/apache2/mods-enabled/${module}.load

We just created a new list called modules. By default it will be empty. We'll
be appending to it in `mybox.yay` later. We then append to resources using a
foreach. Every item in the modules list will add a new :py:class:`yaybu.resources.execute.Execute` resource to
resources.

We provide 3 attributes for our Execute resource. Everything has to have a
unique :py:meth:`yaybu.resources.execute.Execute.name`, and Execute has to
have a :py:meth:`yaybu.resources.execute.Execute.command` to execute. We can also
specify a :py:meth:`yaybu.resources.execute.Execute.creates` attribute. This
is a way of making sure our command is only executed once.

Lets use our recipe in `mybox.yay`::

    yay:
        extends:
            - apache_modules.yay

    modules.append:
        - php5
        - ssl

    resources.append:
        - Package:
            - name: openssh-server
            - name: apache2
            - name: libapache2-mod-php5

yay, our underlying configuration language, has an `extends` list. Currently
the yay section must be the first one in the file for this to work. If
you want you can expand the config and remove all the foreach and variable
expansion. To do this do::

    yaybu --expand-only mybox.yay

You can execute this using the same invokation as before.


Generating VirtualHost files from a template
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

We'll meet the built in Jinja2 based templates and signals.

Here is the new recipe we'll be adding as apache_vhost.yay::

    vhosts: []

    resources.append:
      .flatten
        .foreach vhost in vhosts:
          - File:
              name: /etc/apache2/sites-available/${vhost.name}
              template: package://yaybu.apache/templates/vhost.j2
              template_args:
                  vhost: ${vhost}
          - Link:
              name: /etc/apache2/sites-enabled/${vhost.name}
              to: /etc/apache2/sites-available/${vhost.name}

    resources.append:
        - Execute:
            command: /usr/sbin/apache2ctl graceful
            policy:
                execute.foreach vhost in vhosts:
                    when: apply
                    on: /etc/apache/sites-available/${vhost.name}

Lots of new stuff!

This recipe should do 3 things. Fill in a template called apache_vhost.j2,
link it into the apache2 sites-enabled folder and any time we change
the config file make sure that apache2ctl graceful is called.

To base a file on a template we use the :py:meth:`yaybu.resources.file.File.template`
and :py:meth:`yaybu.resources.file.File.template_args` attributes.
The template_args can be a dict containing any valid yay. We'll see a valid
template in a minute.

While yay is based on YAML it behaves quite differently. While 2 occurences
of resource.append would not be valid in YAML it works just fine in yay.

This time Execute has a policy. We have policies like 'apply' and 'remove'
and can be thought of like like 'Ensure this file is removed if present' or 'Ensure
the following config is applied to a resource'. This example is conditionally
applying the execute policy when the apply policy has occured on one of the
File resources we set up previously. This is how we make sure the apache
graceful step only happens when vhost configuration has changed.

Now lets set up apache_vhost.j2!::

    <VirtualHost {{ vhost.interface }}>
        ServerName {{ vhost.servername }}
        DocumentRoot {{ vhost.root }}
    <VirtualHost>

Pretty straightforward to Django developers, for the rest of us anything
between a pair of {{ }} brackets will be evaluated against whatever we
provided in template_args.

Finally we need to update `mybox.yay` to use it::

    yay:
        extends:
            - apache_modules.yay
            - apache_vhosts.yay

    modules.append:
        - php5
        - ssl

    vhosts:
        - name: customer1.com
          interface: 192.168.201.1
          root: /var/local/sites/customer1.com

        - name: customer2.com
          interface: 192.168.201.1
          root: /var/local/sites/customer2.com

    resources.append:
        - Package:
            - name: openssh-server
            - name: apache2
            - name: libapache2-mod-php5


Seperating the metadata from the configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

We'll polish what we've gotten so far into a reusable config called lamp.yay and
only put the project and specific stuff in `mybox.yay`.

We're going to pretend that we are deploying from an svn server with a sane
repository layout and that the sitename is conventiently the same as the
repository name. We are also using the sitename as the destination directory.

So here is lamp.yay::

    yay:
        extends:
            - apache_modules.yay
            - apache_vhosts.yay

    customers: []

    modules.append:
        - php5
        - ssl

    vhosts:
        .foreach customer in customers:
            name: ${customer.sitename}
            interface: ${host.ip}
            root: /var/local/sites/${customer.sitename}

    resources.append:
        - Package:
            - name: openssh-server
            - name: apache2
            - name: libapache2-mod-php5

    resources.append:
      .flatten:
        .foreach customer in customers:
            - Checkout:
                  name: /var/local/sites/${customer.sitename}
                  repository: http://svn.localhost/${customer.sitename}
                  branch: /tags/${customer.version}


And `mybox.yay` is now::

    yay:
        extends:
            - lamp.yay

    host:
        name: mybox
        ip: 192.168.201.1

    customers:
        - sitename: www.customer1.com
          version: 1.2

        - sitename: www.customer2.com
          version: 1.3

Releasing version 1.4 of customer1.com is a 1 line change to `mybox.yay`
and a yaybu invocation away.


