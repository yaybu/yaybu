=============
YAY Reference
=============

YAY is based on YAML syntax, with extensions to provide a pythonic
macro-language over the top of YAML. This is not as mad as it sounds.

Rationale
=========

Configuration files come in a vast variety of flavours, customised for
specific needs. These vary from the very, very simple (/etc/resolv.conf for
example) to files written in Turing-complete languages (for example, Django
uses Python).

Configuration file languages have to strike a balance between two competing
goals: simplicity and power.

Simplicity
~~~~~~~~~~

On the one hand they need to be simple enough to be used by non-programmers,
and everyone benefits

