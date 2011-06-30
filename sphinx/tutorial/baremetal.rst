================================
Building systems from bare metal
================================

How you build your systems will depend on your choice of OS and distribution -
they each come with their own way of building new systems, for example RedHat's
Kickstart and Debian's Preseed.

However, you will need to decide what you build using the OS specific systems,
and what you build using Yaybu.

We recommend putting as much configuration as possible into Yaybu - this
provides more flexibility and control than maintaining preseeds, because you
are able to roll your changes back to existing live systems easily.

The simplest way of doing this is to manually run yaybu on the newly minted
system using Yaybu Remote.

If you want machines to build themselves from the ground up and enter
production automatically, you will need to do some more.  This will include:

 * Getting authentication keys onto machines as part of the preseed so they can access remote repositories
 * Informing machines of their hostnames using PXEBOOT, so they can select the right configuration
 * Writing an appropriate firstboot.sh shell script that will fetch your configuration and apply yaybu to the correct host file

Security
========

Be aware if using automated builds over PXEBOOT that if an attacker can
convince your build infrastructure to deploy to their systems, they will get
everything!
