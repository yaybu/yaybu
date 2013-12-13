=================
Adding a database
=================

No web application is complete without talking to some kind of database.
We're going to use Postgres for this example.

There are a few working parts to this:

Installing and configuring postgres
===================================

For now we're just going to stick the database on the same VM as the
application.

Create a new file, `postgres.yay`, and put in it::

    extend resources:
    
        - Package:
            - name: postgresql
            - name: libpq-dev
    
        - File:
            name: /etc/postgresql/9.1/main/pg_hba.conf
            static: pg_hba.conf
            owner: postgres
            group: postgres
            mode: 0640
    
        - Execute:
            name: restart-postgres
            command: /etc/init.d/postgresql restart
            policy:
                execute:
                    when: apply
                    on: File[/etc/postgresql/9.1/main/pg_hba.conf]
    
        for name in postgres.databases:
    
            set db = postgres.databases[name]
    
            - Execute:
                name: postgres-create-user
                unless: sh -c "psql -q -c '\du' -t | grep '^ {{name}}'"
                # This allows us to set a password, where createuser doesn't easily
                command: psql -c "CREATE ROLE {{db.username}} PASSWORD '{{db.password}}' NOSUPERUSER NOCREATEDB NOCREATEROLE INHERIT LOGIN"
                user: postgres
    
            - Execute:
                name: postgres-create-database
                unless: sh -c "psql -l | grep '^ {{name}}'"
                command: createdb -O {{db.username}} -E UTF-8 -T template0 {{name}}
                user: postgres
    
You will also need a template pg_hba.conf, that should contain::

    local   all             postgres                                peer
    local   all             all                                     md5
    host    all             all             127.0.0.1/32            md5

You can see from this that postgres is again using a top level key to find it's
configuration. In this case you should add the following to your Yaybufile::

    postgres:
        databases:
            chaser:
                username: chaser
                password: chaser
                


First, we're going to deploy a new version of the chaser code. This one uses a database. Change the branch to deploy in your configuration from::

    branch: part-1

to::

    branch: postgres


