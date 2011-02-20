=========
Resources
=========

Resources are a core concept in Yaybu. You can recognise when a resource is
used in a yay configuration file, because it will be capitalised.


File
====

Manages a local file, its contents, its owner and group and permissions.

name
    A file to create
template
    A jinja2 template
template_args
    Variables accessible from jinja2
static
    A file that is just copied (no templating applied).


Directory
=========

Manages a directory

name
    A directory to create


Link
====

Manages a symbolic link

name
    Where to create a symbolic link
to
    Where to link to


Execute
=======

Manages execution of an external script or binary that might be executing by yaybu. It is expected that this action is idempotent.

name
    A unique name for referring to this Execute by
command
    Command line to execute
cwd
    The directory to execute in
environment
    A map of environment variables to set when executing


Checkout
========

Manages a checkout from a version control system. Currently supports subversion.

name
    Where to checkout to
repository
    URL of the repository
branch
    What branch in the repository to checkout out

