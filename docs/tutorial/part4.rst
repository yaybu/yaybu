============================
Getting closer to production
============================

Part of the purpose of using a system like Yaybu is to get working on something like your planned production stack early, so you can fail fast.

So lets mix in some more of our production stack...

 * Add Nginx to the mix
 * Add some SSL certificates. Unicorn chasers demand security.
 * Ensure our certificate key remains private.

Adding nginx
============

Now lets put Nginx in the mix.

Create a new file. `nginx.yay` alongside your Yaybufile, and put in it::

    extend resources:
        - Package: 
            name: nginx
    
        - File:
            name: /etc/nginx/sites-available/chaser
            template: nginx.j2
            template_args:
                listen: {{app.server.public_ip}}
                name: {{app_name}}.{{devdomain}}
                port: {{port}}
        
        - Link:
            name: /etc/nginx/sites-enabled/chaser
            to: /etc/nginx/sites-available/chaser
    
        - Execute:
            name: reload-nginx
            command: /etc/init.d/nginx reload
            policy:
                execute:
                    when: apply
                    on: File[/etc/nginx/sites-available/chaser]
    
        - Execute:
            name: start-nginx
            command: /etc/init.d/nginx start
            policy:
                execute:
                    when: install
                    on: Package[nginx]
    

You can see this refers to an nginx configuration file template `nginx.j2`.
Create this file with the following contents::

    server {
        listen {{listen}}:80;
        server_name {{name}};
    
        location / {
            proxy_pass http://127.0.0.1:{{port}};
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        }
    }

This is a really common pattern for Yaybu: using a template for part of your
stack's configuration, with included yay files encapsulating the machinery for
deploying it.

The search path
===============

Yaybu has a "search path", just like UNIX' $PATH variable, or Pythons sys.path.
This is a list of directories, URLs and other kinds of places that Yaybu will
search for an item. It does this in order. This allows you to override any
includes by placing a file of the same name in a location with a higher
priority in the search path.

In our case here, we just want to ensure that nginx.yay and nginx.j2 can be
found, so we add the following to the top of our Yaybufile::

    yaybu:
        searchpath:
            - .

This puts the current directory (`.`) as the only item on the search path.

SSL added and removed here :)
=============================

No website should be served without SSL of course,  so lets make sure our
software works ok with it.

SSL is often problematic from a dev environment perspective, and so it’s
generally left till last. Leaving things till last is a recipe for discovering
they don’t work of course. Lets not do that.

We’re going to need to put some thought into this though. Different domains
need different certificates, some of these certificate will have keys that need
to be kept safe. We’re going to ensure all our keys remain protected no matter
what.

To begin with though, lets just roll some “snake oil” certificates and get them
working.

Produce a key::

    $ openssl genrsa -out local.dev.key 2048
    Generating RSA private key, 2048 bit long modulus
    ......+++
    .....+++
    e is 65537 (0x10001)

Then create a wildcard CSR for the local.dev domain, using this key::

    $ openssl req -new -key local.dev.key -out local.dev.csr
    You are about to be asked to enter information that will be incorporated
    into your certificate request.
    What you are about to enter is what is called a Distinguished Name or a DN.
    There are quite a few fields but you can leave some blank
    For some fields there will be a default value,
    If you enter '.', the field will be left blank.
    -----
    Country Name (2 letter code) [AU]:GB
    State or Province Name (full name) [Some-State]:England
    Locality Name (eg, city) []:York 
    Organization Name (eg, company) [Internet Widgits Pty Ltd]:Yaybu
    Organizational Unit Name (eg, section) []:
    Common Name (e.g. server FQDN or YOUR name) []:*.local.dev
    Email Address []:
    
    Please enter the following 'extra' attributes
    to be sent with your certificate request
    A challenge password []:
    An optional company name []:

Finally, create a certificate based on the CSR::

    $ openssl x509 -req -in local.dev.csr -signkey local.dev.key -out local.dev.crt
    Signature ok
    subject=/C=GB/ST=England/L=York/O=Yaybu/CN=*.local.dev
    Getting Private key

Now we can encrypt the key with GPG and delete the plaintext. 

You will need a GPG key. See TODO for how to set this up, if you've never done this.

For production use you need to encrypt secrets for all of the individuals who
will have access to them. The reference has more information in ## REF ##. Here
we’ll encrypt the key for you only::

    $ gpg -e local.dev.key 
    You did not specify a user ID. (you may use "-r")
    
    Current recipients:
    
    Enter the user ID.  End with an empty line: joe.user@example.com
    
    Current recipients:
    4096R/D84C3B1E 2013-09-20 "Joe User <joe.user@example.com>”
    
    Enter the user ID.  End with an empty line: 

And delete the plaintext key and the CSR, which we no longer need::

    $ rm local.dev.key local.dev.csr

We’re left with two files local.dev.key.gpg and local.dev.crt.

Now lets configure nginx. Here's the new contents of `nginx.j2`::

    server {
        listen {{listen}}:443;
        server_name {{name}};
    
        ssl on;
        ssl_certificate /etc/ssl/certs/local.dev.crt;
        ssl_certificate_key /etc/ssl/private/local.dev.key;
    
        location / {
            proxy_pass http://127.0.0.1:{{port}};
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        }
    }

You can see that we’ve changed the port to 443, turned on ssl and added paths
to the certificate and the key, which we’ve put in the standard Debian
locations.

Now we need to get those files onto the server. Update `nginx.yay` so it looks
like this::


    extend resources:
        - Package: 
            name: nginx
    
        - Package:
            name: ssl-cert
    
        - File:
            name: /etc/ssl/certs/local.dev.crt
            static: local.dev.crt
            owner: root
            group: root
            mode: 644
    
        - File:
            name: /etc/ssl/private/local.dev.key
            static: local.dev.key.gpg
            owner: root
            group: ssl-cert
            mode: 640
    
        - File:
            name: /etc/nginx/sites-available/chaser
            template: nginx.j2
            template_args:
                listen: {{app.server.public_ip}}
                name: {{app_name}}.{{devdomain}}
                port: {{port}}
        
        - Link:
            name: /etc/nginx/sites-enabled/chaser
            to: /etc/nginx/sites-available/chaser
    
        - Execute:
            name: reload-nginx
            command: /etc/init.d/nginx reload
            policy:
                execute:
                    when: apply
                    on: File[/etc/nginx/sites-available/chaser]
    
        - Execute:
            name: start-nginx
            command: /etc/init.d/nginx start
            policy:
                execute:
                    when: install
                    on: Package[nginx]

We’ve added the files (and the ssl-cert package). You can see that the static:
source for the local.dev.key file is local.dev.key.gpg. Yaybu knows to decrypt
these files, using your local gpg-agent. This means anyone for whom the file
has been encrypted can use it, but nobody else.

Now run yaybu up.

You can also see that the secret file contents are not displayed in the output.
Yaybu keeps track of secret material and ensures it is never displayed in
logging or debugging output.

