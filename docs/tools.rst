Tool integration
================

Buildout
--------

The buildout recipe isotoma.recipe.postdeploy embeds a Yaybu driven tool in
your site. This allows your site to provide site-specific configuration
management steps such as linking in additional apache configurations or setting
up cron jobs. For example::

    [buildout]
    parts =
        postdeploy

    [postdeploy]
    recipe = isotoma.recipe.postdeploy
    config = assets/config.yay

The recipe will generate a ``bin/postdeploy`` wrapper in your buildout.


Vagrant
-------

We have written a Vagrant plugin that registers a ``:yaybu`` provisioner with
Vagrant. You can install it through Ruby Gems::

    gem install vagrant-yaybu

The latest version is only tested with Vagrant 1.x.

You can now write Yay directly within your Vagrantfile and have Vagrant deploy
it for you::

    Vagrant::Config.run do |config|
      config.vm.box = "lucid64"

      config.vm.provision :yaybu do |cfg|
        cfg.yay = <<-EOS
          resources.append:
           - Package:
              name: python-all
        EOS
      end
    end

If you ``vagrant up`` this Vagrantfile your fresh VM will have python-all
installed.

There are several settings that Yaybu exposes to vagrant in addition to
``cfg.yay`` example above.

cfg.searchpath
    Adds a directory or http(s) resource to the YAYBUPATH, this is the set of
    locations Yaybu wil search for Yay config files and assets and templates
    referenced by them::

        cfg.searchpath << "http://www.example.com/path_to_assets"

    The default searchpath is the current working directory.

cfg.include
    Instructs Yaybu to include a configuration file. This is relative and all
    locations on the search path are checked until the file is found.

        cfg.include << "path/to/config.yay"

cfg.yay
    Injects inline Yay config into Yaybu. This is a string variable so any Ruby
    string operations are valid.

cfg.python
    In order to be as flexible as possible, vagrant-yaybu has to call python
    code rather than just executing that Yaybu binary. It normally uses the
    system python, and hence the system installed Yaybu. You can use this
    variable to use a virtualenv or buildout maintained python environment
    instead.

