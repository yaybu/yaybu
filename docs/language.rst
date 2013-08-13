====================
Language walkthrough
====================

The language used in your ``Yaybufile`` is called ``yay``. It is YAML-like, but
has templates and pythonic expressions. Some other tools just use a templated
form of YAML, which is powerful. But not as powerful as when these new features
are first class citizens of the language.

In this section we'll skim through some of the important bits.

If you like it, it is packaged as a separate library and can be used in your
own python applications.


Variables
=========

You can refer to any structure through the variable syntax::

    me:
      name: John
      nick: Jc2k

    message: Hello, {{ me.nick }}!


Lazy evaluation
===============

Yay is a non-strict, lazyily evaluated language. This means that expressions are
calculated when they are required not when they are declared::

    var1: 50
    var2: {{ var1 + 5 }}
    var1: 0

In an imperative language ``var2`` would be ``55``. But it is actually ``5``.
Stated like this it seems weird and counterintuitive. So lets see how it is
useful. Imagine you have a firewall recipe saved as ``firewall.yay``::

    firewall:
       allow_pings: true
       open:
         - range: 1.1.1.1/32

    resources:
      - File:
          name: /etc/iptables.conf
          template: iptables.conf.j2
          template_args:
              rules: {{ firewall }}

Now for a contrived reason approved in a secret court your new projects server
can't be pingable. You can't just use your existing ``firewall.yay``... Wait,
you can. In your ``Yaybufile``::

    include "firewall.yay"

    firewall:
        allow_pings: false


