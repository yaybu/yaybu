Tool integration
================

Vagrant
-------

We have written a Vagrant plugin that registers a ":yaybu: provisioner to
Vagrant. You can install it through Ruby Gems::

    sudo gem install vagrant-yaybu

We only support Vagrant 0.8 and VirtualBox 4.1 at this time.

You can now write Yay directly within your Vagrantfile and have Vagrant deploy
it for you::

    Vagrant::Config.run do |config|
      config.vm.box = "lucid32"

      config.vm.provision :yaybu do |foo|
        foo.yay = <<-EOS
          resources.append:
           - Package:
              name: python-all
        EOS
      end
    end

If you ``vagrant up`` this Vagrantfile your fresh VM will have python-all
installed.

