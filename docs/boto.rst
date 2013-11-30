.. _zone:

===================
Amazon Web Services
===================

Unfortunately libcloud only covers the common subset of cloud services. Amazon
customers have other services which are currently unique enough that they are
not on libclouds roadmap.

ElastiCache
===========

The ElastiCache service provides hosted memcache and redis instances. In order
to use it, you need to create a CacheCluster and also set up group based
ingress to allow your EC2 instances to access it::


    new CacheSecurityGroup as elasticache_security:
        name: {{ yaybu.args.instance_name }}-cache

    new CacheIngressRule as elasticache_ingress:
        from: {{ ec2_security }}
        to: {{ elasticache_security }}

    new CacheCluster as elasticache_queue:
        name: {{ yaybu.args.instance_name }}-queue
        num_cache_nodes: 1
        cache_node_type: cache.t1.micro
        engine: redis
        port: 6379
        security_groups:
          - {{ elasticache_security }}


RDS
===

The RDS services provides hosted postgres, mysql, oracle and MSSQL databases.
In order to use it you need a DBInstance and to set up group based ingress from
your EC2 instances::

    new DBSecurityGroup as rds_security:
        name: {{ yaybu.args.instance_name }}-db

    new DBSecurityGroupIngress as rds_ingress:
        from: {{ ec2_security }}
         to: {{ rds_security }}

    new DBCluster as rds_cluster:
        name: {{ yaybu.args.instance_name }}-db
        engine: postgres
        security_groups:
          - {{ rds_security }}

