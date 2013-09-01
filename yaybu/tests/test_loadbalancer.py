import unittest2
import os
import tempfile
import mock
from optparse import OptionParser

from libcloud.loadbalancer.types import State, LibcloudLBError
from libcloud.loadbalancer.base import Driver, LoadBalancer as LB, Member, Algorithm

from yaybu.core.command import YaybuCmd
from yaybu import error
from yaybu.loadbalancer import LoadBalancer


class TestLoadBalancer(unittest2.TestCase):

    def setUp(self):
        MockLoadBalancer.next_id = 0
        MockLoadBalancer.members = {}

        LoadBalancer.extra_drivers['DUMMY'] = MockLoadBalancer
        def _():
            del LoadBalancer.extra_drivers['DUMMY']
        self.addCleanup(_)

    def _config(self, contents):
        f = tempfile.NamedTemporaryFile(delete=False)
        f.write(contents)
        f.close()
        path = os.path.realpath(f.name)
        self.addCleanup(os.unlink, path)
        return path

    def _up(self, config, *args):
        config_file = self._config(config)
        config_dir = os.path.dirname(config_file)
        p = OptionParser()
        y = YaybuCmd(config_file, ypath=(config_dir, ))
        y.verbose = 2
        y.debug = True
        y.opts_up(p)
        return y.do_up(*p.parse_args(list(args)))

    def up(self, config, *args):
        self._up(config, "-s", *args)
        try:
            self._up(config, *args)
        except error.NothingChanged:
            raise RuntimeError("Either simulate wasn't read-only or simulate didn't detect change was required")

        try:
            self._up(config, *args)
        except error.NothingChanged:
            return
        raise RuntimeError("Action wasn't idempotent")

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

