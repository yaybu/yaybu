=========================
Download and installation
=========================

Yaybu is currently *pre-beta*. Use it at your own risk. It might completely
hose your system. You have been warned.

From Source
~~~~~~~~~~~

Yaybu is available on github at:

https://github.com/isotoma/yaybu

Install this using the normal python incantations::

    sudo python setup.py install --prefix=/usr/local


Ubuntu
~~~~~~

Ubuntu users have the option of using our experimental yaybu-nightly PPA::

    sudo add-apt-repository ppa:yaybu-team/yaybu-nightly
    sudo apt-get update
    sudo apt-get install python-yaybu

If you don't have the add-apt-repository in your installation, its
equivalent to::

    cat > /etc/apt/sources.list.d/yaybu.list << EOF
    deb http://ppa.launchpad.net/yaybu-team/yaybu-nightly/ubuntu lucid main
    deb-src http://ppa.launchpad.net/yaybu-team/yaybu-nightly/ubuntu lucid main
    EOF

    sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-keys A899DA54
    sudo apt-get update
    sudo apt-get install python-yaybu

