.. _encryption:

==============================================
Protecting your secrets, keys and certificates
==============================================

Yaybu natively supports the use of GPG as a way to protect both secret variables in your configuration files and the use of encrypted assets when using the :ref:`Provisioner <provisioner>` part.

Installing GPG
==============

On an Ubuntu machine GPG can be installed with::

    sudo apt-get install gnupg

On OSX you can install a pre-built binary produced by the `GPGTools <https://gpgtools.org/>`_ team, or you can install it using `brew <http://brew.sh>`_::

    brew install gnupg


Creating a GPG key
==================

If you want to encrypt your secrets for multiple recipients you will need a GPG key. We tend to follow the advice of Debian when `creating new keys <http://keyring.debian.org/creating-key.html>`_ and as such:

 * You should go for a 4096 bit key
 * You should avoid SHA1 as your preferred hash

You can generate a signing and encryption key has follows::

    paul@jolt:~$ gpg --gen-key
    gpg (GnuPG) 1.4.10; Copyright (C) 2008 Free Software Foundation, Inc.
    This is free software: you are free to change and redistribute it.
    There is NO WARRANTY, to the extent permitted by law.

    gpg: directory `/home/paul/.gnupg' created
    gpg: new configuration file `/home/paul/.gnupg/gpg.conf' created
    gpg: WARNING: options in `/home/paul/.gnupg/gpg.conf' are not yet active during this run
    gpg: keyring `/home/paul/.gnupg/secring.gpg' created
    gpg: keyring `/home/paul/.gnupg/pubring.gpg' created
    Please select what kind of key you want:
       (1) RSA and RSA (default)
       (2) DSA and Elgamal
       (3) DSA (sign only)
       (4) RSA (sign only)
    Your selection? 1
    RSA keys may be between 1024 and 4096 bits long.
    What keysize do you want? (2048) 4096
    Requested keysize is 4096 bits
    Please specify how long the key should be valid.
             0 = key does not expire
          <n>  = key expires in n days
          <n>w = key expires in n weeks
          <n>m = key expires in n months
          <n>y = key expires in n years
    Key is valid for? (0) 0
    Key does not expire at all
    Is this correct? (y/N) y

    You need a user ID to identify your key; the software constructs the user ID
    from the Real Name, Comment and E-mail Address in this form:
        "Heinrich Heine (Der Dichter) <heinrichh@duesseldorf.de>"

    Real name: Paul Ubbot
    E-mail address: pubbot@example.com
    Comment:
    You selected this USER-ID:
        "Paul Ubbot <pubbot@example.com>"

    Change (N)ame, (C)omment, (E)-mail or (O)kay/(Q)uit? O
    You need a Passphrase to protect your secret key.

    We need to generate a lot of random bytes. It is a good idea to perform
    some other action (type on the keyboard, move the mouse, use the
    disks) during the prime generation; this gives the random number
    generator a better chance to gain enough entropy.

    Not enough random bytes available.  Please do some other work to give
    the OS a chance to collect more entropy!  (Need 284 more bytes)
    +++++
    ...............................+++++
    We need to generate a lot of random bytes. It is a good idea to perform
    some other action (type on the keyboard, move the mouse, use the
    disks) during the prime generation; this gives the random number
    generator a better chance to gain enough entropy.
    ......+++++
    .......+++++
    gpg: /home/paul/.gnupg/trustdb.gpg: trustdb created
    gpg: key D770E8A9 marked as ultimately trusted
    public and secret key created and signed.

    gpg: checking the trustdb
    gpg: 3 marginal(s) needed, 1 complete(s) needed, PGP trust model
    gpg: depth: 0  valid:   1  signed:   0  trust: 0-, 0q, 0n, 0m, 0f, 1u
    pub   4096R/D770E8A9 2013-08-28
          Key fingerprint = 746B 2477 FB6F CCC6 46C2  D5D2 288C EF6D D770 E8A9
    uid                  Paul Ubbot <pubbot@example.com>
    sub   4096R/49BEE9E3 2013-08-28

You now have a GPG key.

Ideally you should sign the keys of the people you are working with to build a web of trust, however there is no requirement to do so. There are excellent resources online for holding a `key signing event <https://wiki.debian.org/Keysigning>`_.

In order to encrypt for you collaborators will need a copy of the public portion of your key. You can publish your key like so::

    gpg --keyserver subkeys.pgp.net --send-key D770E8A9

Anyone can retrieve your public key like so::

    gpg --keyserver subkeys.gpg.net --recv-keys D770E8A9


Encrypting your configuration
=============================

You might have a ``secrets.yay`` that looks like this::

    secrets:
        aws: somepassword
        rackspace: abetterpassw0rd

You can encrypt it for your new key like this::

    gpg -e -r D770E8A9 secrets.yay

You can use e-mail addresses as well::

    gpg -e -r pubbot@example.com secrets.yay

In both cases a ``secrets.yay.gpg`` will be generated, which you can then reference from your ``Yaybufile``::

    include "secrets.yay.gpg"

    new Compute as myserver:
        driver:
            id: EC2
            key: myawskey
            secret: {{ secrets.aws }}
        <snip>


Encrypting your provisioner assets
==================================

The :ref:`Provisioner <provisioner>` part is GPG aware. If you were copying a file to a server that was a secret you could encrypt it as above and then refer to it from ``File`` parts::

    new Provisioner as p:
        resources:
          - File:
              name: /etc/defaults/foobar
              static: foobar.gpg

In this situation Yaybu would notify you when it changed the file, but it wouldn't show a diff as it knows the file is encrypted and so secret.


Integration with VIM
====================

We are big fans of the `vim-gnupg <https://github.com/jamessan/vim-gnupg>`_ plugin which allows you to::

    vi secrets.yay.gpg

It will transparently decrypt the file, allow you to edit the text contents, then when you save it will re-encrypt it. It will preserve the same recipients, which is very useful if you are working with a team.

