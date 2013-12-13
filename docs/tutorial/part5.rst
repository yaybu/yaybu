=====================================
Creating our first reusable component
=====================================

A key part in designing any large system is being able to reuse your code in
a manageable way. This saves you time, reduces bugs and makes your code
easier to understand.

`Yay` provides the underlying functionality you need to build reusable
components, but it leaves the details of how you want to do this to you. In
particular what you think of as a component will depend very much on your
problem and how you think about it.

For some problems you may want to deploy a very similar stack multiple times.
In this case the stack itself is a component that you want to encapsulate.

In other instances you might be producing something "multi-tenant", where a
single stack is configured for many different tenants. In this case the
tenant is a component.

We want you to be able to grow a configuration over time without having to do
too much upfront design and planning. The way yay works you can start with
something relatively simple and build it up over time as your requirements
mature and you understand more and more of your problem space.

Rather than lay out a particular way you must work, we leave that up to you.
What we will show here is an example for how this could work for a very low
level component indeed: nginx.

Requirements for an nginx component
===================================

When you create a reusable component, one of the key questions you're going to think about is what "knobs" you are going to want to twiddle. Nginx provides many, many, many knobs in it's configuration file format. You aren't going to want to provide all of these options in Yay - if you have no idea of what you might want to share or standardise, then don't even try.

You probably have some idea of what you are going to want to do in a repeatable fashion though. For our example, we want to take our existing configuration and make it just a bit easier to set up multiple sites without doing a lot of copying and pasting.

In the case of the configuration we have already, it's pretty clear that we have some "setup" steps that get nginx installed and ready, and then there are some "per-site" configurations that we apply.

For now we just want to be able to create nginx configurations for proxies,
so all we need is::

 * a name, for ease of reference
 * an interface to listen on
 * the port number on localhost the site we're proxying is on
 * SSL certificates
 * A hostname

There are lots of other options we might want to add later, but lets start
with this and iterate.

What an API looks like in Yay
=============================

Yay only has a single namespace, but all of it (apart from "resources" and "yaybu") is available for your use.

For nginx we're going to use "nginx" as a top level key for our nginx component to find out what it needs to do.

We're going to work with this structure::

    nginx:
        sites:
            - name: <the site name>
              host: <the hostname to listen for>
              port: <the port to forward to>
              listen: <the interface>
              cert: <prefix of the certificate filename>

We'll always put our ssl certificates in the standard Ubuntu locations::

    /etc/ssl/certs/<name>.crt
    /etc/ssl/private/<name>.key

Also we're going to use Debian/Ubuntu's standard sites-available structure.

Here is a very simple nginx component that uses this interface::
    
    extend resources:
        - Package:  
            name: nginx
        
        - Package:
            name: ssl-cert
    
        for site in nginx.sites:
    
            - File:
                name: /etc/nginx/sites-available/{{site.name}}
                template: nginx.j2
                template_args:
                    listen: {{site.listen}}
                    name: {{site.host}}
                    port: {{site.port}}
                    cert: {{site.cert}}
        
            - Link:
                name: /etc/nginx/sites-enabled/{{site.name}}
                to: /etc/nginx/sites-available/{{site.name}}
        
            - Execute:
                name: reload-nginx
                command: /etc/init.d/nginx reload
                policy:
                    execute:
                        when: apply
                        on: File[/etc/nginx/sites-available/{{site.name}}]
    
        - Execute:
            name: start-nginx
            command: /etc/init.d/nginx start
            policy:
                execute:
                    when: install
                    on: Package[nginx]
    
Calling the component
=====================

To use this component in your Yaybufile, you need to include it, as before, but now some of the config goes into the Yaybufile::

    include "nginx.yay"

    nginx:
        extend sites:
            - name: chaser
              listen: {{app.server.public_ip}}
              host: {{app_name}}.{{devdomain}}
              port: {{port}}
              cert: {{devdomain}}

And that's it!

