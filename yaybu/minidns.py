import dns
from libcloud.common.base import Connection
from libcloud.dns.base import DNSDriver, Zone, Record

class MiniDNSConnection(Connection):

    host = "localhost"
    port = 5080
    secure = 0
    request_path = '/'
    ua = []

    def __init__(self, *args, **kwargs):
        pass



class MiniDNSDriver(DNSDriver):

    name = 'minidns'
    connectionCls = MiniDNSConnection

    def __init__(self):
        DNSDriver.__init__(self, None)

    def iterate_zones(self):
        for domain in self.connection.request("").object.split("\n"):
            yield Zone(id=domain, domain=domain + ".", type="master", ttl=0, driver=self)

    def iterate_records(self, zone):
        for record in self.connection.request(zone.domain, method="GET").object.split("\n"):
            if record:
                name, value = record.split()
                yield Record(id=name, name=name, type="A", data=value, zone=zone, driver=self)

    def create_zone(self, domain, type="master", ttl=None, extra=None):
        response = self.connection.request(domain, method="PUT")
        if response.status == 201:
            return Zone(id=domain, domain=domain, type="master", ttl=0, driver=self)

    def update_zone(self, zone, domain, type="master", ttl=None, extra=None):
        return self.create_zone(domain, type, ttl, extra)


    def create_record(self, name, zone, type, data, extra=None):
        response = self.connection.request("%s/%s" % (zone.domain, name), data=data, method="POST")
        if response.status == 201:
            return Record(id=name, name=name, type="A", data=data, zone=zone, driver=self)

