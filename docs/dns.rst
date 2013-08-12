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


Setting up a DNS zone on Gandi
------------------------------

This example creates a VM on bigv, installs git on it and then sets up a `Gandi
<https://www.gandi.net/>`_ DNS Zone for that VM::

    new Provisioner as vm1:
        new Compute as server:
            driver:
                id: BIGV
                key: yourusername
                secret: yourpassword
                account: youraccountname

            image: precise
            name: test123456

            user: root
            password: aez5Eep4

        resources:
          - Package:
              name: git-core

    new Zone as dns:
        driver:
            id: GANDI
            key: yourgandikey

        domain: example.com

        records:
          - name: www
            data: {{ vm1.server.public_ip }}
