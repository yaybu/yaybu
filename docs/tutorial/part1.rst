==========
Smoke test
==========

 * Learn about the types of target you can manage with Yaybu
 * Set up a new Yaybu configuration
 * Test that everything is working

Targets
=======

Yaybu is able to deploy to a number of different targets. Which you choose will
depend on your needs.

At the time of writing Yaybu can deploy to:

 * Bare Metal
 * VMWare
 * Amazon EC2

TODO LIST THEM ALL

For our examples we’ll be using VMWare locally. This means you need VMWare
installed. There are several VMWare products, but if you’ve never used VMWare
before then you will need VMWare Player, their free version. VMWare is
unfortunately proprietary, but it is otherwise the best virtualization stack
available for Linux today.

To see if you have something compatible installed run::

    $ vmrun list

If you get any output at all, you're probably good to go, otherwise install one
of the VMWare products (Player, Server or Workstation). Player is free.

When you download or create virtual machines using Yaybu, the machines and
their disk images are placed in ~/.yaybu. You can see the vms that you have
running with::

    vmrun list

And you can stop them if you need to with::

vmrun stop

Setting up our new configuration
================================

As we work through this book we are going to assemble a typical production
stack for a web application. The web application code itself is already
written.  What we’re going to do is wire it all together into something that
can be managed.

The application itself is a site for people to share and rate Unicorn Chasers.

To get started, create a new directory somewhere called “chaserconf”, and then put a file called Yaybufile inside it containing the following::

    new Provisioner as app:
        new Compute as server:
                    name: app
                    driver: VMWARE
                    image:
                        id: http://yaybu.com/library/ubuntu-12.04.3-server-amd64.zip
                    user: ubuntu
                    password: password
            resources:
              - Package:
                name: python2.7

Then, in that directory, run::

    $ yaybu up

When this is run, if everything is working, you will get output something like::

    $ yaybu up
    [*] Testing compute credentials/connectivity                                    
    [*] Cloning template VM                                                         
    [*] Starting VM                                                                 
    [*] Waiting for VM to boot completely                                           
    [*] Applying new password credentials                                           
    [*] Creating node ''app1''...                                                   
    [*] Waiting for node ''app1'' to start...                                       
    [*] Connecting to '192.168.213.148'                                             
    [*] Applying configuration... (1/1)              

If you get errors, take a look at the troubleshooting section.

We now have a VM running that Yaybu is managing. You can log into it and take a
look around.  Yaybu can provide an ssh session for you. You use a yay
expression to specify the machine you want to connect to, and we will explore
this more later. For now, though, just type::

    $ yaybu ssh app

And you’ll get a login prompt on the VM. The password is, you guessed it, ‘password’.

