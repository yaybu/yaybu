========
Security
========


Handling secret files
=====================

.. todo:: security technique


Handling secret passwords
=========================

Sometimes you want to put a password in a template or pass it to a command
line tool. It's not fantastic, but theres no sense in making it worse by
logging the password to the screen as well! Yaybu supporrts GPG encrypted
configuration. Any passwords in an encrypted yay file will be marked as
sensitive and not displayed on screen.

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
    | $ /bin/echo *****
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

