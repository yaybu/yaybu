Infrastructure as Python
========================

You might not want to use Yay as your configuration language if you are building
a web application with deployment capabilities. You might be generating config
based on database query results or similar. If Yay is not suitable then you can
directly drive Yaybu from python::

    from yaybu.core.whitehat import *
    from yaybu.core.remote import RemoteRunner

    File(
        name = "/example",
        )

    def example_method(sitename):
        Directory(
            name = "/var/www/{sitename}",
            )

        File(
            name = '/var/www/{sitename}/touchme",
            )

    for site in ("www.foo.com", "www.bar.com", ):
        example_method(site)

    r = RemoteRunner()
    rv = r.run(ctx, get_bundle())


.. todo:: This documentation deliberately doesn't define ctx: We don't yet have
          a public stable API for that.

In the example we get all currently registered resources by importing them from
the whitehat module. These are special proxies that automatically register the
resources with a ResourceBundle.

As you can see implied in ``example_method``, we sneakily ``.format(**locals())``
any strings passed to the resource. This will make your configuration so so
much prettier.

When we have finished adding things to the bundle we create a ``RemoteRunner()``
and apply the config.

