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

This is implemented using `libcloud<http://libcloud.apache.org/>`_. 


Inputs
======

``driver``

You must specify a ``domain``.

``ttl``

``extra``

``records``


Supported services
==================


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

