============
Contributing
============

Join us on IRC
==============

We are in ``#oftc`` on ``irc.oftc.net``.


Getting the source
==================

The source code is available on GitHub - please fork it and send us pull requests!

The main components you might want to hack on are:

========= ================================================================
Component Description
========= ================================================================
yaybu     The main app. You'll need to change this to add new CLI subcommands or add new ``Parts``.
yay       The configuration language runtime. You will need to change this to improve parsing, the runtime graph, file transports, etc.
yaybu.app This contains a small OSX application and build scripts to package Yaybu for OSX. You will probably need to fork this to fix OSX specific bugs.


