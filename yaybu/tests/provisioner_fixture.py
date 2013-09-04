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

import os
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

        from yaybu.provisioner import Provision
        Provision.Transport = FakechrootTransport

        filespath = os.path.join(self.chroot_path, "/tmp", "files")
        from yaybu.core.command import YaybuCmd
        from optparse import OptionParser

        p = OptionParser()
        y = YaybuCmd(configfile, ypath=(filespath, ))
        y.verbose = 2
        y.debug = True
        y.opts_up(p)

        return y.do_up(*p.parse_args(list(args)))

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

    def check_apply(self, contents, *args, **kwargs):
        # Apply the change in simulate mode
        sim_args = list(args) + ["-s"]
        self.apply(contents, *sim_args)

        # Apply the change for real
        self.apply(contents, *args)

        # If we apply the change again nothing should be changed

        try:
            self.apply(contents, *args)
        except error.NothingChanged:
            return

        raise CalledProcessError("Change still outstanding")


class TestCase(unittest2.TestCase):

    FakeChroot = YaybuFakeChroot
    location = os.path.join(os.path.dirname(__file__), "..", "..", "..")

