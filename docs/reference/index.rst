=========
Reference
=========

.. todo:: reference introduction

Running yaybu
=============

.. todo:: running yaybu


Resources
=========

Resources are a core concept in Yaybu.

A Resource is a thing on your deployment target that can be described in
an abstract way and then be managed by Yaybu without any explicit migration
scripts being written. You define the state you want the resource to be in
and yaybu will work out how to get it there.

The management yaybu can range from something like ensure a symbolic link
exists, to applying templates to files, to making sure the right tag
of your Plone site is checked out to anything that can be expressed in
python.

You can recognise when a resource is used in a yay configuration file,
because it will be capitalised.

.. toctree::
   :maxdepth: 1

   resources/package
   resources/execute
   resources/file
   resources/directory
   resources/link
   resources/special
   resources/user
   resources/group
   resources/checkout
   resources/service
   resources/prompt

Command line arguments
======================

You can specify that additional arguments can be provided to yaybu, which are
made available to your configuration.

You should specify the following in your configuration::

    yaybu:
        options:
            - name: <name>
              type: <type name from list of types below>
              help: <help text shown to the user>
              default: <default value>
              

For example:

    yaybu:
        options:
            - name: version
              type: string
              help: The version of software to deploy
              default: trunk

You can then pass these arguments to yaybu as name=value pairs on the command line::

    yaybu provision ... version=tag/1.0
    
The values provided by the user will be made available in the key yaybu.argv,
for the example above this would look like::

    yaybu:
        argv:
            version: tag/1.0
       
Argument types
--------------

 string
   The argument will be provided as a string
 integer
   The argument will be converted into an integer
 boolean
   The argument will be converted into a boolean. All common english ways of specifying booleans are supported (0, 1, yes, no, on, off etc.)
   
   
Deploying to the cloud
======================

When Yaybu is used to deploy to cloud infrastructures such as AWS, Yaybu
populates a set of configuration terms with the configuration of these hosts,
so that your configuration can refer to it.

We recommend that you build all of your configurations against such an API,
so that if you ever do wish to deploy existing configurations to the cloud
you can do so.

Defining your cloud
-------------------

You need to specify the names of the clouds and sufficient details about them
so that appropriate instances can be started::

    clouds:
        <name>:
            default: <true if this is to be the default cloud>
            providers:
                compute: <name of libcloud compute provider>
                storage <name of libcloud storage provider>
                dns: <name of libcloud dns provider>
            args:
                <arguments to provide to the providers>
            images:
                <your name>: <their name>
            sizes:
                <your name>: <their name>
            keys:
                <key name>: <url of key file>

Roles
-----

Initially you will need to define the roles you wish to deploy. This is used
by Yaybu to determine how many hosts, and of what type, to start at your
chosen cloud service.

Your roles should look like::

    roles:
    
        <name>:
            key: <name of ssh key to use>
            instance:
                image: <image name to use>
                size: <size name to use>
            include:
                - <path to yay file to include when deploying to this role>
            max: <maximum number of this role allowed to run>
            min: <minimum number of this role allowed to run>
            dns:
                zone: <zone that the server will exist in>
                name: <host name within the zone>

Provided configuration
----------------------

Yaybu will create a set of terms that looks like this::

    yaybu:
        provider:
        cluster:
        argv:
        
    hosts:
        