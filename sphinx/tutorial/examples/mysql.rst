=============
MySQL example
=============


Installing it and setting the root password
===========================================

This recipe is specfically for Debian and Ubuntu systems and will use debconf
to seed various settings for the mysql server. Open up `mysql.yay`::

    resources.append:
      - Directory:
          name: /var/cache/yaybu
          mode: 0755

      - File:
          name: /var/cache/yaybu/mysql-server.seed
          template: mysql/mysql-server.seed.j2
          template_args:
              root_password: ${mysql.root_password}

      - Execute:
          name: seed-mysql-server
          command: debconf-set-selections /var/cache/yaybu/mysql-server.seed
          policy:
            execute:
              when: apply
              on: File[/var/cache/yaybu/mysql-server.seed]


The seed file (`mysql/mysql-server.seed.j2`) looks like this::

    mysql-server mysql-server/root_password select {{ root_password }}
    mysql-server mysql-server/root_password_again select {{ root_password }}


Back to `mysql.yay`: lets actually install mysql::

    resources.append:
      - Package:
          - name: mysql-server
          - name: mysql-client


Creating databases
==================

We are going to add a list of databases and setup Yaybu to automatically create
all the databases in that list. We'll also make it idempotent. It will only
try to create a database if id doesn't exist already.

So still in `mysql.yay`::

    databases: []

    resources.append:
       .foreach db in databases:
          Execute:
            name: create-${db}
            command: mysql -u root --password='${mysql.root_password}' -e "CREATE DATABASE ${db}"
            unless: mysql -u root --password='${mysql.root_password}' -e "connect ${db}"


Keeping your root password safe
===============================

At some point you are going to have to set `mysql.root_password`. We suggest you do it in a
secure yay file that is encrypted with GPG. This will stop Yaybu from printing your password
in the logs. See :doc:`/techniques/security` for details of this technique.


