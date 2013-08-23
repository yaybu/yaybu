================
Installing Yaybu
================

Latest stable release
=====================

.. warning: The version of Yaybu described in this documentation is currently not available as a stable release.
Ubuntu
------

The latest release is packaged as ``deb`` packages and is available via a PPA for recent versions of Ubuntu::

    sudo add-apt-repository ppa:yaybu-team/stable
    sudo apt-get update
    sudo apt-get install python-yaybu


OSX
---

A ``.dmg`` is available from the `releases <https://github.com/isotoma/yaybu/releases>`_ page at GitHub.

Drag the Yaybu icon into your Applications folder. When you first run Yaybu it will prompt you to install command line tools. This will simply create a symlink from ``/usr/local/bin/yaybu`` to command line tools embedded inside the Yaybu bundle.

You can drop ``Yaybufile`` files onto the Yaybu dock icon to automatically start a Yaybu shell for a project.


Nightlies
=========

Ubuntu
------

An unstable 'nightly' PPA is available for lucid and precise. You can use it like this::

    sudo add-apt-repository ppa:yaybu-team/nightly
    sudo apt-get update
    sudo apt-get install python-yaybu

OSX
---

The latest build is available from `here <https://yaybu.com/nightlies/osx/Yaybu-latest.dmg>`_. Install it like you would install a stable version.

It's automatic update feed is pointed at the nightlies channel.

