=======================
Getting into production
=======================

Yaybu is designed to manage the *configuration* of a system. This means things like:

 * the configuration of the base Operating System: networking, email, etc.
 * the software that is installed and the versions of that software
 * the configuration of the installed applications

It is not appropriate for conducting one-off or ad hoc system administration
tasks. If you want to copy a file or review log files, don't use Yaybu for
that.

When implementing Yaybu you should decide on the scope that is appropriate for
your needs.  We recommend of course managing as much of your configuration as
possible, to get the maximum benefits from the system.

Contents:

.. toctree::
   :maxdepth: 1

   structuring
   baremetal
   remote
