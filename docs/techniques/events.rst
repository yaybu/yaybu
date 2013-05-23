======
Events
======

Event subscription allows you to respond to Yaybu applying config.
For example, you might want to restart apache when you update one
of its configuration files.

A simple example is::

    extend resources::
      - File:
          name: /etc/apache2/sites-enabled/www.example.com
          template: vhost.j2
          template_args:
            sitename: www.example.com

      - Execute:
          name: apache2-graceful
          command: apache2ctl graceful
          policy:
            execute:
              when: apply
              on: File[/etc/apache2/sites-enabled/www.example.com]


