# Copyright 2011-2013 Isotoma Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os, subprocess
from unittest2 import SkipTest
from yaybu import error

from fakechroot import unittest2


class CalledProcessError(Exception):
    pass


class YaybuFakeChroot(unittest2.FakeChroot):

    """
    I provide a very simple COW userspace environment in which to test configuration

    I am used for some of Yaybu's internal tests.
    """

    Exception = SkipTest

    def yaybu(self, configfile, *args):
        from yaybu.provisioner.transports import FakechrootTransport
        FakechrootTransport.env = self.get_env()
        FakechrootTransport.chroot_path = self.chroot_path
        FakechrootTransport.overlay_dir = self.overlay_dir

        from yaybu import Provision
        Provision.Transport = FakechrootTransport

        filespath = os.path.join(self.chroot_path, "/tmp", "files")
        from yaybu.core.command import YaybuCmd
        from optparse import OptionParser

        # import logging
        # logging.basicConfig(format="%(asctime)s %(name)s %(levelname)s %(message)s")
        # root = logging.getLogger()
        # root.setLevel(logging.DEBUG)

        p = OptionParser()
        y = YaybuCmd(configfile, ypath=(filespath, ))
        y.verbose = 2
        y.debug = True
        y.opts_up(p)
        try:
            return y.do_up(*p.parse_args(list(args)))
        except SystemError:
            return 0

    def simulate(self, configfile, *args):
        """ Run yaybu in simulate mode """
        args = ["--simulate"] + list(args)
        return self.yaybu(configfile, *args)

    def apply(self, contents, *args):
        path = self.write_temporary_file(contents)[0]
        path2 = self.write_temporary_file(
            """
            include "%s"
            main:
                new Provisioner:
                    server:
                        fqdn: fakechroot:///
                    resources: {{ resources }}
            """ % path)[0]

        return self.yaybu(path2, *args)

    def apply_simulate(self, contents):
        path = self.write_temporary_file(contents)[0]
        path2 = self.write_temporary_file(
            """
            include "%s"
            main:
                new Provisioner:
                    server:
                        fqdn: fakechroot:///
                    resources: {{ resources }}
            """ % path)[0]

        return self.simulate(path2)

    def check_apply(self, contents, *args, **kwargs):
        expect = kwargs.get('expect', 0)

        # Apply the change in simulate mode
        sim_args = list(args) + ["-s"]
        rv = self.apply(contents, *sim_args)
        if rv != expect:
            raise CalledProcessError("Simulation failed: got rv %s" % rv)

        # Apply the change for real
        rv = self.apply(contents, *args)
        if rv != expect:
            raise CalledProcessError("Apply failed: got rv %s" % rv)

        # If 'expect' isnt 0 then theres no point doing a no-changes check
        if expect != 0:
            return

        # If we apply the change again nothing should be changed
        rv = self.apply(contents, *args)
        if rv != error.NothingChanged.returncode:
            raise CalledProcessError("Change still outstanding")

    def check_apply_simulate(self, contents):
        rv = self.apply_simulate(contents)
        if rv != 0:
            raise CalledProcessError("Simulate failed rv %s" % rv)


class TestCase(unittest2.TestCase):

    FakeChroot = YaybuFakeChroot
    location = os.path.join(os.path.dirname(__file__), "..", "..", "..")

