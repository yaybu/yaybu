=======
Roadmap
=======

Release + 1
===========

Our primary aim for release+1 is a switch away from the compute focused
server-in-isolation approach towards an abstract 'clusters of parts' model.
Each unit within a cluster is underpinned by a 'part' which is provisioned in
dependency order to create a cluster. In this model the ability to provision
compute parts with an idempotent DSL is just one ability.

You will be able to chain these together and express dependencies through yay::

    parts:
      web2:
        class: compute
        param1: 1

      web1:
        class: compute
        param1: 2

      loadbalancer:
        class: lb
        members:
         - ${parts.web1}
         - ${parts.web2}

      dns:
        class: compute
        records:
         - name: www
           type: CNAME
           data: ${parts.loadbalancer.dnsname}

The next major release of Yaybu will be marked by the inclusion of a major new
version of yay, the DSL that underpins it. This will fix many of the edge cases
and stylistic warts of the current version and allow even more expressive and
declarative cluster definitions.

To aid integration with web services we'll ship a proof-of-concept integration
with a django-tastypie API.


Internals
---------

Internally we will be cleaning up the myriad of ways to invoke Yaybu. The
``apply`` and ``push`` commands will be updated to use the new parts/cluster
API and reduce the number of codepaths to test.
i


Parts
-----

We are aiming to ship with a good spread of default part types in this release,
including:

State
~~~~~

Amazon: S3
Dedicated: Files
Others: Files on Brightbox

Compute
~~~~~~~

Amazon: EC2
Dedicated: Computers
Others: Brightbox, Fedora Cobbler

LoadBalancer
~~~~~~~~~~~~

Amazon: ELB
Dedicated: HAProxy
Others: Brightbox load balancing service

DNS
~~~

Amazon: Route 53
Dedicated: BIND
Others: GANDI

Bucket Storage
~~~~~~~~~~~~~~

Amazon: S3
Dedicated: Files?
Others: Nimbus.io

RDBMS
~~~~~

Amazon: RDS
Dedicated: Postgres
Others: Heroku? Postgres on Brightbox




Release 2
=========

Cloudfront
Elasticache
SQS
EBS

Release 3
=========

Cloudwatch
Elastic beanstalk
Cloudsearch
Autoscaling
