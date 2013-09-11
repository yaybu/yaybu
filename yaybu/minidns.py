import dns
from libcloud.common.base import Connection
from libcloud.dns.base import DNSDriver, Zone, Record, RecordType

class MiniDNSConnection(Connection):

    host = "localhost"
    port = 5080
    secure = 0
    request_path = '/'
    ua = []

    def __init__(self, *args, **kwargs):
        pass



class MiniDNSDriver(DNSDriver):

    """Driver for the local MiniDNS Service. See

    https://github.com/yaybu/minidns
    """


    name = 'minidns'
    connectionCls = MiniDNSConnection



    def __init__(self):
        DNSDriver.__init__(self, None)

    def list_record_types(self):
        # minidns only supports A records right now
        return [RecordType.A]

    def iterate_zones(self):
        for domain in self.connection.request("").object.split("\n"):
            yield Zone(id=domain, domain=domain + ".", type="master", ttl=0, driver=self)

    def iterate_records(self, zone):
        for record in self.connection.request(zone.domain, method="GET").object.split("\n"):
            if record:
                type_, name, value = record.split()
                yield Record(id=name, name=name, type=type_, data=value, zone=zone, driver=self)

    def get_zone(self, zone_id):
        domain = zone_id.rstrip(".")
        response = self.connection.request(domain, method="GET")
        if response.status == 200:
            return Zone(id=domain, domain=domain, type="master", ttl=0, driver=self)

    def create_zone(self, domain, type="master", ttl=None, extra=None):
        domain = domain.rstrip(".")
        response = self.connection.request(domain, method="PUT")
        if response.status in (200, 201):
            return Zone(id=domain, domain=domain, type="master", ttl=0, driver=self)

    def update_zone(self, zone, domain, type="master", ttl=None, extra=None):
        return self.create_zone(domain, type, ttl, extra)

    def create_record(self, name, zone, type, data, extra=None):
        # not going to call __repr__ for this, sorry chaps
        reverse = dict((v, k) for k, v in list(RecordType.__dict__.items()))
        payload = "%s %s" % (reverse[type], data)
        domain = zone.domain.rstrip(".")
        uri = "%s/%s" % (domain, name)
        response = self.connection.request(uri, data=payload, method="PUT")
        if response.status == 201:
            return Record(id=name, name=name, type=type, data=data, zone=zone, driver=self)

    def update_record(self, record, name, type, data, extra=None):
        return self.create_record(name, record.zone, type, data, extra)

    def delete_zone(self, zone):
        domain = zone.domain.rstrip(".")
        response = self.connection.request(domain, method="DELETE")
        if response.status == 204:
            return True
        return False


