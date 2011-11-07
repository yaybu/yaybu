Tool integration
================

Vagrant
-------

The Yaybu source code comes with a Vagrant provisioner. Until this is merged
upstream we currently suggest keeping it in the same directory as your
Vagrantfile.

We only support Vagrant 0.8 and VirtualBox 4.1 at this time.

You can write Yay directly within your Vagrantfile and have Vagrant deploy it
for you::

    require 'yaybu_provisioner'

    Vagrant::Config.run do |config|
      config.vm.box = "lucid32"

      config.vm.provision YaybuProvisioner do |foo|
        foo.yay = <<-EOS
          resources.append:
           - Package:
              name: python-all
        EOS
      end
    end

If you ``vagrant up`` this Vagrantfile your fresh VM will have python-all
installed.

