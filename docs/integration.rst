====================================
Integration with third party service
====================================

Provisioning on commit via Travis CI
====================================

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

