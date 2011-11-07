require 'yaml'
require 'pty'

$deploy_script = <<-EOS
#! /usr/bin/env python

import sys, StringIO
from yay.config import Config
from yaybu.core.remote import RemoteRunner
from yaybu.core.runcontext import RunContext

raw_config = StringIO.StringIO("""
<%= yay %>
""")

config = Config()
config.load(raw_config)

class opts:
    log_level = "info"
    logfile = "-"
    host = "<%= ssh_user %>@<%= ssh_host %>:<%= ssh_port %>"
    user = "root"
    ypath = []
    simulate = False
    verbose = False
    resume = True
    no_resume = False
    env_passthrough = []

ctx = RunContext(None, opts)
ctx.set_config(config)

r = RemoteRunner()
r.set_interactive(False)
r.set_identity_file("<%= private_key_path %>")
r.set_missing_host_key_policy("no")
r.load_host_keys("/dev/null")
rv = r.run(ctx)
sys.exit(rv)

EOS


class YaybuError < Vagrant::Errors::VagrantError
    error_namespace("vagrant.provisioners.yaybu")
end


class YaybuProvisioner < Vagrant::Provisioners::Base
  class Config < Vagrant::Config::Base
    attr_accessor :yay
    attr_accessor :python

    def initialize
      @yay = ""
    end
  end

  def bootstrap
    vm.ssh.execute do |ssh|
      begin
        ssh.sudo!("which yaybu", :error_class => YaybuError, :_key => :yaybu_not_detected, :binary => "yaybu")
      rescue
        env.ui.info "Yaybu not found so attmpting to install it"
        ssh.sudo!("apt-get update")
        ssh.sudo!("apt-get install python-setuptools -y")
        ssh.sudo!("easy_install Yaybu")
      end
    end
  end

  def prepare
  end

  def provision!
    bootstrap

    #print config.config.to_yaml

    deployment_script = TemplateRenderer.render_string($deploy_script, {
      :ssh_host => vm.env.config.ssh.host,
      :ssh_user => vm.env.config.ssh.username,
      :ssh_port => vm.ssh.port,
      :private_key_path => vm.env.config.ssh.private_key_path,
      :yay => config.yay,
      })

    IO.popen("python -", "r+") do |io|
      io.write(deployment_script)
      io.close_write

      while line = io.gets do
        env.ui.info("#{line}")
      end
    end

  end
end

