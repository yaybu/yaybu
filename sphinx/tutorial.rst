Tutorial
========

Worked Example
--------------

We have a computer "mybox" on which we wish to deploy a simple PHP application
from Subversion, based on tagged versions of the php content.

The following file expresses this configuration:

mybox.yay::

    yaybu:
        versions:
            yaybu.apache: 1
            yaybu.mysql: 1
            yaybu.firewall: 1

    distro:
        base: Ubuntu 10.04.1 LTS
        packages:
            - openssh

    firewall:
        recipe: yaybu.firewall
        open-ports:
            - ssh

    apache:
        recipe: yaybu.apache
        enable-modules:
            - php5
            - ssl
        virtual-hosts:
                - name: www.example.com
                  server-name: www.example.com
                  customlog: /var/log/apache2/www.example.com.log combined
                  errorlog: /var/log/apache2/www.example.com.error.log
                  document-root: /var/local/www.example.com/htdocs

    content:
        recipe: yaybu.scm
        name: /var/local/www.example.com
        repository: https://svn.example.com/example
        branch: /tags/1.1.1
        user: www-data

    # todo, add some mysql stuff to create a database and user and load a
    # schema if the database does not exist

The recipes specified above are also defined in yay.  The recipe files specify
which resources need to exist and be configured for the recipe to work. For
example, the following recipe is for apache::

    recipe: yaybu.apache
    description: installs and configures apache

    firewall:
        open-ports.append:
            - 80

    resources.append:
        .foreach virtual-hosts as vhost:
            - File:
                name: /etc/apache2/sites-available/${vhost.name}
                template: package://yaybu.apache/templates/vhost.j2
                template_args:
                    server-name: ${vhost.server-name}
                    customlog: ${vhost.customlog}
                    errorlog: ${vhost.errorlog}
                    document-root: ${vhost.document-root}
            - Link:
                name: /etc/apache2/sites-enabled/${vhost.name}
                to: ../sites-available/${vhost.name}

    resources.append:
        - Package:
            - name: apache2
        - Execute:
            command: /usr/sbin/apache2ctl graceful
            when.foreach virtual-hosts as vhost:
                - resource: File[/etc/apache2/sites-available/${vhost.name}]

This recipe specifies what the system should look like once the recipe is
applied.  For example, that the apache2 package should be installed, port 80
opened in iptables and a file and symlink created.

The recipe is provided as part of a python package.  The template is located
using the python module name resolution namespace.

The terms with capital letters in the recipe are Resources. Resources are
registered by python packages also: each resource specifies an interface for a
Provider.

Providers provide a resource when a certain set of criteria match. If two
providers both match then an error is thrown.

For example, the following specification in a recipe::

    Scm:
        repository: http://svn.example.com/foo

could be fulfilled by any provider that uses a URL for a repository. In these
cases you should specify the scm client::

    Scm:
        client: subversion
        repository: http://svn.example.com/foo

In other cases it will depend on the target system::

    Package:
        - apache2

This will install an rpm on RedHat systems and a deb on Debian systems. in this
case distro.base will be inspected to determine which packaging commands will
be issued.


