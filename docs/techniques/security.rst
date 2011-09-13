========
Security
========

There are 2 main techniques for dealing with secrets in Yaybu. Both
encourage you to keep your secrets in a GPG encrypted format in
your configuration repository.


Handling secret files
=====================

If you want to securely deploy a secret (for example an SSL cert) you
can do so with the encryption support built in to the File provider.

.. note::

   To use the feature you will need to have set up a GPG key.

Encrypt your secret with gpg::

    $ gpg -e mysecret.key

GPG will ask for receipients. These are the people able to decrypt this file.
You should add anyone that will be deploying this configuration. For now
just add yourself.

It should create a mysecret.key.gpg.

If you want to verify that the encryption was successful you can decrypt
and compare it to the original. Here we do it by comparing a digest::

    $ gpg --decrypt mysecret.key.gpg | md5sum
    bea8252ff4e80f41719ea13cdf007273  -

    $ md5sum mysecret.key
    bea8252ff4e80f41719ea13cdf007273  test

You should either delete the original or keep it someone very secure.
The encrypted variant should be safe to keep in version control, but
that depends on who has access to it.

To use this in your configuration you would add::

    resources.append:
     - File:
         name: /etc/ssl/private/mysecret.key
         encrypted: mysecret.key.gpg
         mode: 0400

Please be careful with file modes. There is no sense encrypting something
if you then deploy it with world-read permissions!

When you deploy a configuration that uses this technique Yaybu won't
show diffs for encrypted files. When using Yaybu Remote the decryption
will happen on the operators machine, and the secret will be transmitted
securely over SSH.


Handling secret passwords
=========================

Sometimes you want to put a password in a template or pass it to a command
line tool. It's not fantastic, but theres no sense in making it worse by
logging the password to the screen as well! Yaybu supporrts GPG encrypted
configuration. Any passwords in an encrypted yay file will be marked as
sensitive and not displayed on screen.

.. note::

   To use this feature you will need to have set up a GPG key.

Make a new file called secrets.yay::

    secret: password

And encrypt it with GPG::

    $ gpg -e secrets.yay

GPG will ask you for recipients. These are the people able to decrypt
the secrets file. For the purposes of this example, use the email address
of your GPG key.

You should now have a secrets.yay.gpg. You should probably delete secrets.yay.

Now lets write some configuration that uses these secrets. Edit config.yay::

    yay:
      extends:
        - secrets.yay.gpg

    resources.append:
      - Execute:
          name: test
          command: echo ${secret}

      - File:
          name: /tmp/test
          template: simple.j2
          template_args:
            secret: ${secret}

      - File:
          name: /tmp/control
          template: simple.j2
          template_args:
            secret: I am a control example

We define 3 resources. 2 show how Yaybu takes care to not leak your secrets,
and the 3rd shows the normal behaviour still applies to resources not utilising
secrets.

Our template simple.j2 is simply::

    The secret is: {{secret}}

Lets run yaybu and see what happens::

    $ sudo yaybu config.yay -v
    /-------------------------------- Execute[test] --------------------------------
    | # /bin/echo *****
    | password
    \-------------------------------------------------------------------------------

    /------------------------------- File[/tmp/test] -------------------------------
    | Writting new file '/tmp/test'
    \-------------------------------------------------------------------------------

    /----------------------------- File[/tmp/control] ------------------------------
    | Writting new file '/tmp/control'
    |     ---
    |     +++
    |     @@ -1,0 +1,1 @@
    |     +The secret is: I am a control example
    \-------------------------------------------------------------------------------

It hid the password, but it can't help it if the script you call out to leaks it. It
also hid the template diff because it contained a secret. But the control example didn't
have a secret, so that still logs a diff. Success!

When using Yaybu Remote, any decryption will happen on the operators machine, not on
the target machine. In is sent to the target server securely over SSH.

