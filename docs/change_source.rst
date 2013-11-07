==============
Change Sources
==============

EXPERIMENTAL: Provisioning on commit (via Travis CI)
====================================================

Travis CI has a mechansim to encrypt secrets. It also has a hook that is run on
success. This means we can have yaybu perform system orchestration tasks on
commit + successful CI run without having to run any of our own servers.

Here is a simple ``Yaybufile``::

    yaybu:
        options:
            - name: BIGV_KEY
            - name: BIGV_SECRET
            - name: BIGV_ACCOUNT
            - name: BIGV_ROOT_PASSWORD
              default: penguin55

    new Provisioner as myexample:
        new Compute as server:
            driver:
                id: BIGV
                key: {{ yaybu.argv.BIGV_KEY }}
                secret: {{ yaybu.argv.BIGV_SECRET }}

            image: precise

            name: myexample

            user: root
            password: {{ yaybu.argv.BIGV_ROOT_PASSWORD }}

        resources:
          - Package:
              name: git-core

          - Checkout:
             name: /tmp/yaybu
             scm: git
             repository: https://github.com/yaybu/example

The ``yaybu.options`` section allows us to define arguments that can be passed
to yaybu via the command line. You can define defaults to use if no such
argument is passed in.

Now we can encrypt these details using the travis command line tool::

    travis encrypt BIGV_KEY=myusername --add env.global
    travis encrypt BIGV_SECRET=password --add env.global
    travis encrypt BIGV_ACCOUNT=myaccount --add env.global
    travis encrypt BIGV_ROOT_PASSWORD=password --add env.global

And here is what your ``.travis.yml`` looks like::

    language: python
    pythons:
      - "2.6"

    env:
      global:
        - secure: <YOUR_ENCRYPTED_STRINGS>

    script:
      - true # This is where you would normally run your tests

    after_success:
      - sudo add-apt-repository yaybu-team/yaybu
      - sudo apt-get update
      - sudo apt-get install python-yaybu
      - yaybu up BIGV_KEY=$BIGV_KEY BIGV_SECRET=$BIGV_SECRET BIGV_ACCOUNT=$BIGV_ACCOUNT BIGV_ROOT_PASSWORD=$BIGV_ROOT_PASSWORD


EXPERIMENTAL: Provisioning on commit
====================================

This uses a new command, ``yaybu run``. This puts yaybu into a mode where it
continues to run, rather than deploying then exiting. Parts can set up
listeners to respond to external events like commits or monitoring systems.

To deploy on commit you can use a ``Yaybufile`` like this::


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
             revision: {{ changesource.master }}


The ``GitChangeSource`` part polls and sets ``{{changesource.master}}`` with
the SHA of the current commit.

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

