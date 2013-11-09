Deploying us some Django
========================

Create a directory, cd into it and slip into your favourite editor to create a
file called ‘Yaybufile’. Type in the following::

    # The details of the application we're going to deploy
    repo: https://github.com/yaybu/chaser.git
    branch: part-1
    
    # The Operating System we're deploying to
    server_image: http://yaybu.com/library/ubuntu-12.04.3-server-amd64.zip
    
    # The development domain servers will appear under
    devdomain: local.dev
    
    # Where we are deploying to: http://chaser.local.dev:8000
    app_user: ubuntu
    app_name: chaser
    app_dir: /home/ubuntu/chaser
    pidfile: {{app_dir}}/chaser.pid
    port: 8000
    listen: 0.0.0.0:{{port}}
    
    start_command: >
        ./bin/python manage.py
        run_gunicorn {{listen}}
        --pid={{pidfile}} -D
    
    stop_command: >
        test -e {{pidfile}} && 
        kill `cat {{pidfile}}` && 
        rm {{pidfile}} || 
        /bin/true
    
    # A zone 
    new Zone as local:
        driver: MINIDNS
        domain: {{devdomain}}
        records:
            - name: {{app_name}}
              data: {{app.server.public_ip}}
    
    # The instance we're going to put our things on
    new Compute as app_server:
        name: {{app_name}}
        driver: VMWARE
        image:
            id: {{server_image}}
        user: ubuntu
        password: password
    
    resources:
    
        - Package:
            - name: git-core
            - name: python-virtualenv
    
        - Checkout:
            name: {{app_dir}}
            scm: git
            repository: {{repo}}
            branch: {{branch}}
            user: {{app_user}}
    
        - Execute:
            name: virtualenv
            command: virtualenv .
            cwd: {{app_dir}}
            user: {{app_user}}
            creates: {{app_dir}}/bin/activate
    
        - Execute:
            name: rebuild-restart
            commands: 
                - ./bin/pip install -r requirements.txt
                - {{stop_command}}
                - {{start_command}}
            cwd: {{app_dir}}
            user: {{app_user}}
    
    new Provisioner as app:
        server: {{app_server}}
        resources: {{resources}}
    
Save it, and get your minidns server running if it isn’t already::

    $ minidns start

Then::

    $ yaybu up

While it runs, lets walk through this Yaybufile. First we define a bunch of
things that will come in useful later::

    # The details of the application we're going to deploy
    repo: https://github.com/winjer/chaser.git
    branch: part-1
    
    # The Operating System we're deploying to
    server_image: http://yaybu.com/library/ubuntu-12.04.3-server-amd64.zip
    
    # The development domain servers will appear under
    devdomain: local.dev

    # Where we are deploying to
    app_user: ubuntu
    app_name: chaser
    app_dir: /home/ubuntu/chaser
    pidfile: {{app_dir}}/chaser.pid
    listen: 0.0.0.0:8000

Then we need some way of starting and stopping Django. We are using Green
Unicorn, which is well integrated with Django.

This runs a webserver on port 8000 of all interfaces, and writes it’s PID out
to the pidfile::

    start_command: >
        ./bin/python manage.py
        run_gunicorn {{listen}}
        --pid={{pidfile}} -D

And this will kill a running process if there is one::

    stop_command: >
        test -e {{pidfile}} && 
        kill `cat {{pidfile}}` && 
        rm {{pidfile}} || 
        /bin/true

Now we need to find our web application on our virtual network. For that we
create a zone in MiniDNS::

    new Zone as local:
        driver: MINIDNS
        domain: {{devdomain}}
        type: master
        ttl: 60
        records:
            - name: {{app_name}}
              type: A
              data: {{app.server.public_ip}}

The URL is going to be http://{{app_name}}.{{devdomain}}:8000, e.g. http://chaser.local.dev:8000.

The next bit is to define a server on which we’re going to install our
components::

    new Compute as app_server:
        name: {{app_name}}
        driver: VMWARE
        image:
            id: {{server_image}}
        user: ubuntu
        password: password

Then we define the resources we’re going to deploy to this server::

    resources:
    
        - Package:
            - name: git-core
            - name: python-virtualenv
    
        - Checkout:
            name: {{app_dir}}
            scm: git
            repository: {{repo}}
            branch: {{branch}}
            user: {{app_user}}
    
        - Execute:
            name: virtualenv
            command: virtualenv .
            cwd: {{app_dir}}
            user: {{app_user}}
            creates: {{app_dir}}/bin/activate

        - Execute:
            name: rebuild-restart
            commands:
                - ./bin/pip install -r requirements.txt
                - {{stop_command}}
                - {{start_command}}
            cwd: {{app_dir}}
            user: {{app_user}}

And finally we need a Provisioner, to provision our components onto the server.
All the provisioner needs is to know where to provision the things, and which
things to provision::

    new Provisioner as app:
        server: {{app_server}}
        resources: {{resources}}

The first time you run this, yaybu will download the specified packed vm, clone
it to a brand new VM, start it and then run all of the appropriate commands.
The VM will be left running so the next time you deploy it will be much faster.

Yaybu examines the current state of the system and only applies the changes
necessary to bring your system up to the state you have requested. This means
that often running Yaybu will be idempotent: that nothing will be touched if it
doesn’t need to be.

Yaybu should have finished running by now, and you should have a running
virtual machine with a Django application running on it.

You can go to http://chaser.local.dev:8000 to see it.

When you run Yaybu a second time, you will get much less output because it has
already done most of the work. It doesn't preserve it's own state to work this
out, it introspects the state of the machine::

    $ yaybu up
    [*] Testing DNS credentials/connectivity                                        
    [*] Testing compute credentials/connectivity                                    
    [*] Updating 'chaser'                                                           
    [*] Connecting to '192.168.213.148'                                             
    /---------------------------- Execute[pip-install] -----------------------------
    | # ./bin/pip install -r requirements.txt                                       
    | Requirement already satisfied (use --upgrade to upgrade): Django in ./lib/python2.7/site-packages (from -r requirements.txt (line 1))
    | Requirement already satisfied (use --upgrade to upgrade): gunicorn in ./lib/python2.7/site-packages (from -r requirements.txt (line 2))
    | Cleaning up...                                                                
    \-------------------------------------------------------------------------------
    /---------------------------- Execute[kill-django] -----------------------------
    | # test -e /home/ubuntu/chaser/chaser.pid && kill `cat /home/ubuntu/chaser/chaser.pid` && rm /home/ubuntu/chaser/chaser.pid || /bin/true
    \-------------------------------------------------------------------------------
    /---------------------------- Execute[start-django] ----------------------------
    | # ./bin/python manage.py run_gunicorn 0.0.0.0:8000 --pid=/home/ubuntu/chaser/chaser.pid -D
    \-------------------------------------------------------------------------------
    [*] Applying configuration... (7/7)                                             

It's kind of annoying that it does anything at all though really.

Events and policies
===================

Lets tidy it up a bit. First, we only want to stop and start Django if we’ve
changed anything. This means, only run the stop and start if our Checkout
actually synced. Change the final Execute step to::

       - Execute:
            name: rebuild-restart
            commands: 
                - ./bin/pip install -r requirements.txt
                - {{stop_command}}
                - {{start_command}}
            cwd: {{app_dir}}
            user: {{app_user}}
            policy:
                execute:
                    when: sync
                    on: Checkout[{{app_dir}}]

And Yaybu will only re-run pip and restart Django if there have been any code
changes, because the Checkout resource will only emit a sync event if there
have been changes.

Try this yourself - run yaybu up and it shouldn't make any changes at all.








