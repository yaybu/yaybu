=============================
Managing cloud load balancers
=============================

Yaybu can manage your load balancers using a ``LoadBalancer`` part. They run as soon as all of the inputs become valid, as opposed to when the program encounters them.

A basic setup looks like this::

    new LoadBalancer as lb:
        name: myprojectlb

        driver:
            id: ELB
            key: yourawskey
            secret: yourawssecret

        # Listen on port 80 for http access
        port: 80
        protocol: http
        algorithm: round-robin

        members:
          - {{ server1 }}


Options
=======

You must specify a ``name`` when creating a ``LoadBalanacer`` part. Some backends will use this as a unique id for the load balancer. Take care to avoid duplicating load balancer names in different configurations!

The ``driver`` section contains the settings used by libcloud to initialize a driver. This typically includes account information - a access key and secret, a username and password, or similar.

You must specify a ``port`` for the load balancer to listen on.

The load balancer needs to know what ``protocol`` it is balancing. For example, if it is handling SSL connections it can act as an SSL terminator but to do this it needs to know it is an SSL protocol. Not all balancers support all protocols, and Yaybu doesn't expose SSL support at the moment. You can set ``protocol`` to one of:

 * ``http``
 * ``https``
 * ``tcp``
 * ``ssl``

Some load balancers let you choose an ``algorithm``. This is the method by which the load balancer distributes traffic. It can be one of:

``random``
    Incoming connections are assigned to a backend at random
``round-robin``
    Incoming connections are passed to a backend in a circular fashion without any considering of priority.
``least-connections``
    Incoming connections are passed to the backend with the least number of active connections with the assumption that it must have the most free capacity.
``weighted-round-robin``
    Same as ``round-robin``, but also factors in a weight factor for each member
``weighted-least-connections``
    Same as ``least-connections``, but also factors in a weight factor for each member

The ``members`` input is a list of all compute resources that load will be spread over. There are a few variations here.

If you are doing load balancing for port 80 and forwarding to port 80 on the backend VM's then you can::

    new LoadBalancer as lb:
        <snip>
        members:
          - {{ server1 }}
          - {{ server2 }}

In this example ``server1`` and ``server2`` are ``Compute`` parts defined elsewhere in your configuration.

However if you are using different ports on the backend servers you can::

    new LoadBalancer as lb:
        <snip>
        members:
          - instance: {{ server1 }}
            port: 8080

Not all backends support this, and an error will be raised before deployment starts if it is not.

There are 2 main types of cloud load balancer. The first accepts IP addresses and ports. If you pass a ``Compute`` node to this type of load balancer Yaybu will determine it's IP automatically. But you can pass ip addresses manually::

    new LoadBalancer as lb:
        <snip>
        members:
          - ip: 192.168.0.1
            port: 8080

Other load balancers expect to be give a list of compute instance ids. Again, Yaybu will do the right thing if given ``Compute`` parts. But you can also give it ``id`` values directly::

    new LoadBalancer as lb:
        <snip>
        members:
          - id: ec2123ab
            port: 8080


Outputs
=======

The part exposes a number of output variables to other Yaybu parts.

Each load balancer that is created has a unique ``id``. In some cases this may be the same as the ``name``.

A load balancer has a ``public_ip``. This is the public facing method of accessing the load balancer.


Supported services
==================

Using libcloud to implement this part allows us to support a number of DNS services. Some of these receive more extensive real world testing than others and are listed in this section.

Elastic Load Balancing
----------------------

The driver id for Elastic Load Balancing is ``ELB``::

    new LoadBalancer as lb:
        name: my-load-balancer

        driver:
            id: ELB
            key: myaccesskey
            secret: myaccesssecret
            region: eu-west-1

        port: 80
        protocol: http
        algorithm: round-robin

        # The default is just a
        ex_memebers_availability_zones:
          - a
          - b

        members:
          - id: ec2123

For this driver:

 * After creating a balancer you cannot change its settings (you can continue to add and remove members).
 * ``protocol`` must be either ``tcp`` or ``http``.
 * ``algorithm`` must be ?.....?
 * ``members`` are managed by instance id. You cannot set the backend port.
 * ``ex_members_availability_zones`` is an ELB specific extension that controls which Amazon availabilty zones a balancer is in.


Community supported services
============================

By using libcloud to support the services in the previous section, the following services are also available:

Brightbox
---------

The driver id for brightbox is ``BRIGHTBOX``::

    new LoadBalancer as lb:
        name: my-load-balancer

        driver:
            id: BRIGHTBOX
            key: acc-43ks4
            secret: mybrightboxsecret

        port: 80
        protocol: http
        algorithm: round-robin

        members:
          - id: ec2123

For the Brightbox loadbalancer:

 * ``protocol`` must be ``http`` or ``tcp``
 * ``algorithm`` must be ``round-robin`` or ``least-connections``
 * ``members`` are managed by instance id, and you cannot set the backend port (your backends must listen on the same port as your load balancer).


Cloudstack
----------

The driver id for cloudstack is not currently set upstream, so it is currently unavailable.

For the CloudStack loadbalancer:

 * After creating a balancer you cannot change its setting (you can continue to add and remove members).
 * ``protocol`` must be ``tcp``
 * ``algorithm`` must be ``round-robin`` or ``least-connections``
 * ``members`` are managed by instance id. You cannot set the backend port.


GoGrid
------

The driver id for GoGrid is ``GOGRID``::

    new LoadBalancer as lb:
        name: my-load-balancer

        driver:
            id: GOGRID
            key: myaccesskey
            secret: myaccesssecret

        port: 80
        protocol: http
        algorithm: round-robin

        members:
          - id: ec2123

For this driver:

 * ``protocol`` must be ``http``
 * ``algorithm`` must be ``round-robin`` or ``least-connections``
 * ``members`` are managed by ip. Each backend can use a different port.


Ninefold
--------

The driver id for Ninefold is ``NINEFOLD``::

    new LoadBalancer as lb:
        name: my-load-balancer

        driver:
            id: NINEFOLD
            key: myaccesskey
            secret: myaccesssecret

        port: 80
        protocol: http
        algorithm: round-robin

        members:
          - id: ec2123

Ninefold uses CloudStack, so see that section for additional notes.


Rackspace
---------

The driver id for Rackspace load balancing is ``RACKSPACE_UK``::

    new LoadBalancer as lb:
        name: my-load-balancer

        driver:
            id: RACKSPACE_UK
            key: myaccesskey
            secret: myaccesssecret

        port: 80
        protocol: http
        algorithm: round-robin

        members:
          - id: ec2123

For this driver:

 * After creating a balancer you can later change its settings.
 * The list of supported ``protocol`` options is dynamic and fetched from Rackspace at runtime.
 * ``algorithm`` must be one of ``random``, ``round-robin``, ``least-connections``, ``weighted-round-robin`` or ``weighted-least-connections``.
 * ``members`` are managed by ip/port pairs.

