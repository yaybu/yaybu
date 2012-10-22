# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant::Config.run do |config|
  config.vm.box = "precise64"
  config.vm.box_url = "http://files.vagrantup.com/precise64.box"
  
  config.vm.define :yaybu do |cfg|
    cfg.vm.network :hostonly, "10.33.32.2"
    cfg.vm.forward_port 22, 3333     # real ssh
  end
end

