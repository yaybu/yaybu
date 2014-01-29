==============
Change Sources
==============

Change sources listen to remote repositories for commits and tags, allowing you
to trigger a deployment as code is committed.

Change sources require you to run yaybu in 'active mode', using the ``yaybu
run`` command.

GitChangeSource
===============

The ``GitChangeSource`` polls any git repostory that can be accessed using
``git ls-remote``. By default it will do this every 60s. A typical example of
how to use this might be::


    new GitChangeSource as changesource:
        polling-interval: 10
        repository: https://github.com/isotoma/yaybu

    new Provisioner as myexample:
        new Compute as server:
            driver:
                id: EC2_EU_WEST
                key: mykey
                secret: mysecret

            size: t1.micro
            image: ami-000cea77

            ex_keyname: mysshkey
            name: myexample

            user: ubuntu
            private_key: mysshkey.pem

        resources:
          - Package:
              name: git-core

          - Checkout:
             name: /tmp/yaybu
             scm: git
             repository: {{ changesource.repository }}
             revision: {{ changesource.branches.master }}


The ``GitChangeSource`` part polls and sets
``{{changesource.branches.master}}`` with the SHA of the current commit.

This example changesource polls to learn if a new commit has occurred. This is
only because the part is an example implementation - it could easily be a
webhook or zeromq push event.

The ``Checkout`` resource uses the ``master`` property of ``changesource``.
Yaybu can use this dependency information to know that the ``Provisioner`` that
owns the ``Checkout`` is stale and needs applying every time ``master``
changes.

If your Yaybufile contained another ``Provisioner`` that didn't have such a
``Checkout`` (perhaps its the database server) then Yaybu would equally know
*not* to deploy to it on commit.

