from yaybu.resource.filesystem import File as FileResource
import yaybu.provider.filesystem
from yaybu.core import shell
import sys
import logging
logging.basicConfig(stream=sys.stdout,level=logging.DEBUG)

def resources():
    return [
        FileResource(name="/tmp/wibble",
                     owner="doug",
                     group="doug",
                     mode="666"),
        FileResource(name="/tmp/interfaces",
                     owner="root",
                     group="root",
                     mode="644",
                     template="recipe://yaybu.distro/interfaces.j2",
                     template_args = {
                         "interfaces": [
                             {"name": "eth0",
                              "type": "static",
                              "auto-up": "yes",
                              "address": "83.142.228.46",
                              "netmask": "255.255.255.0",
                              "network": "83.142.228.0",
                              "broadcast": "83.142.228.255",
                              "gateway": "83.142.228.1",
                            },
                             {"name": "eth0:0",
                              "type": "static",
                              "auto-up": "yes",
                              "address": "83.142.228.16",
                              "netmask": "255.255.255.0",
                            },
                             {"name": "eth1",
                              "type": "dhcp",
                              "auto-up": "yes",
                            },
                        ]
                     })
        ]


if __name__ == '__main__':
    import optparse
    parser = optparse.OptionParser()
    parser.add_option("-s", "--simulate", default=False, action="store_true")
    opts, args = parser.parse_args()
    s = shell.Shell(simulate=opts.simulate)
    for r in resources():
        p = r.select_provider(None)
        p.action_create(s)
