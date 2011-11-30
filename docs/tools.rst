Tool integration
================

Vagrant
-------

We have written a Vagrant plugin that registers a ``:yaybu`` provisioner with
Vagrant. You can install it through Ruby Gems::

    gem install vagrant-yaybu

We only support Vagrant 0.8 and VirtualBox 4.1 at this time.

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
    code rather than just executing that Yaybu binary. This variable lets you
    set which variable. We use this to let us use virtualenv or buildout
    generated python environments.

