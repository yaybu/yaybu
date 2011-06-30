=============
MySQL example
=============


Installing it and setting the root password
===========================================

This recipe is specfically for Debian and Ubuntu systems and will use debconf
to seed various settings for the mysql server. Open up mysql.yay::

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


The seed file (mysql/mysql-server.seed.j2) looks like this::

    mysql-server mysql-server/root_password select {{ root_password }}
    mysql-server mysql-server/root_password_again select {{ root_password }}


Lets actually install mysql::

    resources.append:
      - Package:
          name: mysql-server


