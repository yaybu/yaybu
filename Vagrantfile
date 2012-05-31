# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant::Config.run do |config|
  config.vm.box = "lucid64"

  config.vm.customize ["modifyvm", :id, "--memory", "1024"]

  config.vm.define :yaybu do |web_config|
    web_config.vm.network :hostonly, "10.33.32.2"
    
    web_config.vm.forward_port 22, 3333     # real ssh

  end

end

