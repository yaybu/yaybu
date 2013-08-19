.. _zone:

========================
Managing cloud based DNS
========================

Yaybu can manage your DNS using a ``Zone`` part. A basic setup looks like this::

    new Zone as mydns:
        driver:
            id: GANDI
            key: yourgandikey

        domain: example.com

        records:
          - name: mail
            data: 173.194.41.86
            type: A

          - name: www
            data: www.example.org
            type: CNAME

In this example, when you run ``yaybu apply`` this part will look for a zone named ``example.com`` and create it if it does not exist. It will ensure that all the ``records`` given exist and are of the right ``type`` and have the right ``data``.


Options
=======

Use the ``driver`` argument to find and initialize a libcloud DNS driver. You must specify an ``id`` so that the right service is targetted. Other variables include users and secrets and are described in the service-specific notes below.

You must specify a ``domain``. If a zone for this domain doesn't exist it will be created.

You must provide a list of DNS ``records`` to publish in the zone. At the very least you will specify a ``name`` and ``data`` but other options are available:

``name``
    For example ``www`` or ``pop``. You do not need to specify a fully qualified domain name.
``type``
    The type of DNS record - for example ``A`` or ``CNAME``.
``data``
    The data to put in the DNS record. This varies between record types, but is typically an IP address for ``A`` records or a fully qualified domain name for a ``CNAME`` record.
``ttl``
    How long this record can be cached for, specified in seconds. Specifying ``86400`` seconds would mean that if a DNS record was changed some DNS servers could be returning the old value for up to 24 hours.


Supported services
==================

Using ``libcloud`` to implement this part allows us to support a number of DNS services. Some of these receive more extensive real world testing than others and are listed in this section.

Gandi
-----

The driver id for `Gandi<http://www.gandi.net/>`_ is ``GANDI``::

    new Zone as dns:
        driver:
            id: GANDI
            key: yourgandikey

        domain: example.com

        records:
          - name: www
            data: 192.168.0.1

TTL can only be set on records.

Gandi supports the following record types:

 * NS
 * MX
 * A
 * AAAA
 * CNAME
 * TXT
 * SRV
 * SPF
 * WKS
 * LOC


Route53
-------

The driver id for `Route53<http://aws.amazon.com/route53/>`_ is ``ROUTE53``::

    new Zone as dns:
        domain: example.com

        driver:
            id: ROUTE53
            key: youraccountkey
            secret: youraccountsecret

        records:
          - name: www
            data: 192.168.0.1

TTL can only be set on records.

Route53 supports the following record types:

 * NS
 * MX
 * A
 * AAAA
 * CNAME
 * TXT
 * SRV
 * PTR
 * SOA
 * SPF
 * TXT


Community supported services
============================

By using `libcloud` to support the services in the previous section, the following services are also available:


HostVirtual
-----------

The driver id for `HostVirtual<http://www.vr.org/>`_ is ``HOSTVIRTUAL``::

    new Zone as dns:
        domain: example.com

        driver:
            id: HOSTVIRTUAL
            key: yourkey
            secret: yoursecret

        records:
          - name: www
            data: 192.168.0.1

TTL can be set by zone and by record.

HostVirtual supports the following recort types:

 * A
 * AAAA
 * CNAME
 * MX
 * TXT
 * NS
 * SRV


Linode
------

The driver id for `Linode<https://www.linode.com/wiki/index.php/Linode_DNS>`_ is ``LINODE``::

    new Zone as dns:
        domain: example.com

        driver:
            id: LINODE
            key: yourlinodeikey
            secret: yourlinodesecret

        records:
          - name: www
            data: 192.168.0.1

TTL can be set by zone and by record.

Linode supports the following record types:

 * NS
 * MX
 * A
 * AAAA
 * CNAME
 * TXT
 * SRV


RackSpace
---------

The driver id for `Rackspace DNS<http://www.rackspace.com/cloud/dns/>`_ is ``RACKSPACE_UK`` or ``RACKSPACE_US``::

    new Zone as dns:
        domain: example.com

        driver:
            id: RACKSPACE_UK
            user_id: rackspace_user_id
            key: rackspace_secret_key

        records:
          - name: www
            data: 192.168.0.1

TTL can be set by zone and by record.

Rackspace supports the following record types:

 * A
 * AAAA
 * CNAME
 * MX
 * NS
 * TXT
 * SRV


Zerigo
------

The driver id for `Zerigo<http://www.zerigo.com/managed-dns>`_ is ``ZERIGO``::

    new Zone as dns:
        domain: example.com

        driver:
            id: ZERIGO
            key: youraccountkey
            secret: youraccountsecret

        records:
          - name: www
            data: 192.168.0.1

TTL can be set by zone and by record.

Zerigo supports The following record types:

 * A
 * AAAA
 * CNAME
 * MX
 * REDIRECT
 * TXT
 * SRV
 * NAPTR
 * NS
 * PTR
 * SPF
 * GEO
 * URL

