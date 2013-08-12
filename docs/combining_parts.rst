===============
Combining parts
===============

You can combine the parts in different ways using the ``yay`` language.


Create and provision a cloud server
===================================

You can use a ``Compute`` part to provide the ``server`` key of the ``Provisioner`` part::

    new Provisioner as vm1:
        new Compute as server:
            name: mytestvm1
            driver:
                id: VMWARE
            image:
                id: /home/john/vmware/ubuntu/ubuntu.vmx
            user: ubuntu

        resources:
          - Package:
              name: git-core

When the ``Provisioner`` part tries to access ``server.fqdn`` the ``Compute`` part will automatically find an existing ``mytestvm1`` or create a new one if needed.


Create a new instance and automatically set up DNS
==================================================

You can use the IP from a ``Compute`` part in other parts just by using it like any other variable::

    new Compute as server:
        name: mytestserver
        driver:
            id: EC2
            key: secretkey
            secret: secretsecret
        image: imageid
        size: t1.micro

    new Zone as dns:
        driver:
            id: ROUTE53
            key: secretkey
            secret: secret
        domain: mydomain.com
        records:
          - name: www
            type: A
            data: {{ server.public_ip }}


Create and provision interdependent cloud servers
=================================================

You can refer to server A from the configuration for server B and vice versa and Yaybu will satisfy the dependcies automatically::

    new Provisioner as vm1:
        new Compute as server:
            name: mytestvm1
            driver:
                id: VMWARE
            image:
                id: /home/john/vmware/ubuntu/ubuntu.vmx
            user: ubuntu

        resources:
          - File:
              name: /etc/foo
              template: sometemplate.j2
              template_args:
                  vm2_ip: {{ vm2.server.public_ips[0] }}

    new Provisioner as vm2:
        new Compute as server:
            name: mytestvm2
            driver:
                id: VMWARE
            image:
                id: /home/john/vmware/ubuntu/ubuntu.vmx
            user: ubuntu

        resources:
          - File:
              name: /etc/foo
              template: sometemplate.j2
              template_args:
                  vm1_ip: {{ vm1.server.public_ips[0] }}

Here a templated ``File`` on ``mytestvm1`` needs the IP address of ``mytestvm2``. ``mytestvm2`` needs the IP address of ``mytestvm1``. Yaybu is able to work out that it should activate both ``Compute`` parts first, then proceed to provision both template files to the instances.


