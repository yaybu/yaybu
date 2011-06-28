==================
Remote Deployments
==================

Yaybu comes with a builtin method for deploying to a server without
having to have the cookbook on the target. It also avoids having to
expose your passwords and GPG key on the server.

If you have this configured correctly you just::

    $ yaybu --host boxname.yourdomain.com boxname.yay


What happens when I use Yaybu in remote mode?
=============================================

When you use remote mode Yaybu will SSH into the target machine and
start another Yaybu process remotely. This process will communicate
with the parent Yaybu over the SSH channel. Currently it uses this
channel to:

 * Transmit status messages to the client.
 * Acquire the config to apply
 * Acquire static files and templates from the cookbook
 * Ask for encrypted static files to be decrypted. The decryption
   happens locally so your passphrase is never on the server. The
   data is transmitted over the existing SSH channel so remains
   secure. It is up to you to ensure the secret is appropriately
   locked down (e.g. chmod 0400 the destination file).


How should I configure my server?
=================================

First of all, install yaybu on the remote server.

We strongly suggest using SSH Key based authentication.

The user that you connect as will need to be able to become root. If
you are not connecting as the root user, then you should add it to
sudoers, like this::

    # /etc/sudoers
    #
    # This file MUST be edited with the 'visudo' command as root.
    #
    # See the man page for details on how to write a sudoers file.
    #

    Defaults        env_reset

    # Host alias specification

    # User alias specification

    # Cmnd alias specification
    Cmnd_Alias YAYBU = /usr/bin/yaybu

    # User privilege specification
    root    ALL=(ALL) ALL

    # Allow members of the admin group to run yaybu as root without
    # providing a password
    %admin ALL=(root) NOPASSWD: YAYBU

    # Members of the admin group may gain root privileges
    %admin ALL=(ALL) ALL

