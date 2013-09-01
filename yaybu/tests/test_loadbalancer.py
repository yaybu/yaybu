
from libcloud.loadbalancer.types import State, LibcloudLBError
from libcloud.loadbalancer.base import Driver, LoadBalancer as LB, Member, Algorithm

from yaybu.loadbalancer import LoadBalancer
from yaybu.tests.base import TestCase


class TestLoadBalancer(TestCase):

    def setUp(self):
        self.addCleanup(setattr, MockLoadBalancer, "next_id", 0)
        self.addCleanup(setattr, MockLoadBalancer, "members", {})

        LoadBalancer.extra_drivers['DUMMY'] = MockLoadBalancer
        self.addCleanup(LoadBalancer.extra_drivers.pop, 'DUMMY', None)

    def test_empty_records_list(self):
        self.up("""
            new LoadBalancer as mylb:
                name: my_test_loadbalancer

                driver:
                    id: DUMMY
                    key: hello
                    secret: password

                port: 80
                protocol: http
                algorithm: random
                members: []
            """)


class MockLoadBalancer(Driver):
    name = 'dummy'

    next_id = 0
    balancers = {}

    def __init__(self, key, secret):
        # Need a constructor so HTTP .connect() isn't invoked in base class
        pass

    def list_protocols(self):
        return ['tcp', 'ssl', 'http', 'https']

    def list_supported_algorithms(self):
        return [Algorithm.RANDOM]

    def list_balancers(self):
        return self.balancers.values()

    def create_balancer(self, name, port, protocol, algorithm, members):
        pending_balancer = LB(
            id=str(self.next_id),
            name=name,
            state=State.PENDING,
            ip="192.168.1.2",
            port=port,
            driver=self
        )
        balancer = LB(
            id=str(self.next_id),
            name=name,
            state=State.RUNNING,
            ip="192.168.1.2",
            port=port,
            driver=self
        )
        pending_balancer._members = []
        balancer._members = []
        self.balancers[str(self.next_id)] = balancer
        self.next_id += 1
        return pending_balancer

    def destroy_balancer(self, balancer):
        if not balancer.id in self.balancers.keys():
            raise LibcloudLBError("Balancer does not exist")
        del self.balancers[balancer.id]
        return True

    def get_balancer(self, balancer_id):
        if not balancer_id in self.balancers:
            raise LibcloudLBError("Balancer does not exist")
        return self.balancers[balancer_id]

    def balancer_attach_member(self, balancer, member):
        b = self.get_balancer(balancer.id)
        m = Member(member.id, member.ip, member.port, balancer=b)
        b._members.append(m)
        return m

    def balancer_detach_member(self, balancer, member):
        b = self.get_balancer(balancer.id)
        b._members = [m for m in balancer._members if m.id != member.id]
        return True

    def balancer_list_members(self, balancer):
        return list(balancer._members)

