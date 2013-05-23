========
Security
========

How does yaybu deal with secrets?
=================================

Our preferred strategy is to encrypt them with GPG. You can deploy
secrets securely using the encrypted attribute of the File resources.

This looks something like::

    extend resources:
      - File:
          name: /etc/somesecret
          encrypted: path/in/cookbook.gpg

If you use password based encryption you will be prompted for the password
everytime Yaybu needs to decrypt a secret.

We suggest you use public/private key encryption and a GPG agent (like
seahorse on GNOME). With that set up the user doing a deployment will
only be prompted for their passphrase once.


How does Yaybu deal with SVN and Git securely?
==============================================

We use SSH Agent forwarding.

In particlar we wanted to avoid the --username and --password options of
SVN and the horror of leaving our passwords in .netrc for Git.

The SSH modes of these tools were appealing, but we also felt it unwise to
use passphraseless keys on the deployment target.

We didn't really want to encode passwords for our SCM in our cookbooks either.

SSH Agent forwarding is ideal. It means a deployment's SCM activity can
be authenticated using the SSH credentials of the Op doing a deployment,
and that the authentication can be handled through the vanilla or seahorse
SSH agent software on the Op's desktop.


How does yaybu deal with passwords?
===================================

Very cautiously. We have avoided adding any kind of secret protection to the
cookbook language because we don't want to leak our passwords on the command
line. We don't want to be interactive with programs that require passwords if
at all possible - it feels fragile.

If a secret is going to existing unecrypted on disk (for example, a database
password might find its way into a Django settings.py) then would suggest using
GPG encryption support to deal with it, with 0400 permissions.


How does yaybu obtain root?
===========================

If yaybu is not running as root it will attempt to become root using sudo.
We felt it was better to defer to sudo than add another setuid program
to your system. It means you can control who can run yaybu using standard
sudoers config.

We configure Yaybu to be able to become root without a password.

Yaybu 0.2.0 will add support for configuration signing. This will add an
additional layer of protection should an account able to use Yaybu become
compromised.

