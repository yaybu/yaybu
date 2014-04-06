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
import json
import inspect
import pkgutil
import textwrap

try:
    from unittest2 import SkipTest
except ImportError:
    try:
        from unittest import SkipTest
    except ImportError:
        class SkipTest(Exception):
            pass

from fakechroot import FakeChroot

from yaybu import base
from yaybu.tests.base import TestCase as BaseTestCase
from yaybu.provisioner.transports.remote import stat_result, \
    struct_group, struct_passwd, struct_spwd
from yaybu.provisioner.transports.fakechroot import FakechrootTransport


class TransportRecorder(object):

    # path =...
    # id = ...
    # Transport = ...

    Transport = FakechrootTransport

    def __init__(self, *args, **kwargs):
        self.inner = self.Transport(*args, **kwargs)

    def __getattr__(self, function_name):
        attr = getattr(self.inner, function_name)
        if function_name.startswith("_"):
            return attr

        def _(*args, **kwargs):
            e = None
            try:
                results = attr(*args, **kwargs)
                exception = None
            except KeyError as e:
                results = None
                exception = "KeyError"
            except OSError as e:
                results = None
                exception = "OSError"
            self.results.append((function_name, results, exception))
            if e:
                raise e
            return results
        return _


class TransportPlayback(object):

    # path = ...
    # id = ...

    def __init__(self, *args, **kwargs):
        pass

    def __getattr__(self, function_name):
        f, results, exception = self.results.pop(0)
        assert function_name == f, "'%s' != '%s'" % (function_name, f)

        def _(*args, **kwargs):
            if exception:
                raise {
                    "KeyError": KeyError,
                    "OSError": OSError,
                }[exception]()
            return {
                "stat": lambda x: stat_result(*x),
                "lstat": lambda x: stat_result(*x),
                "getgrall": lambda x: [struct_group(*y) for y in x],
                "getgrnam": lambda x: struct_group(*x),
                "getgrgid": lambda x: struct_group(*x),
                "getpwall": lambda x: [struct_passwd(*y) for y in x],
                "getpwnam": lambda x: struct_passwd(*x),
                "getpwuid": lambda x: struct_passwd(*x),
                "getspall": lambda x: [struct_spwd(*y) for y in x],
                "getspnam": lambda x: struct_spwd(*x),
            }.get(f, lambda x: x)(results)
        return _


class FakeChrootPart(base.GraphExternalAction):

    """
    This part can create and destroy a fakechroot, but via the yay machinery.
    """

    def apply(self):
        location = self.params.location.as_string()

        chroot = self.FakeChroot.create_in_tempdir(location)
        chroot.build()

        self.members['fqdn'] = "fakechroot://" + chroot.chroot_path


class TestCase(BaseTestCase):

    FakeChroot = FakeChroot
    location = os.path.join(os.path.dirname(__file__), "..", "..", "..")
    Transport = None

    def setUp(self):
        self.path = inspect.getfile(self.__class__).rsplit(".", 1)[0] + ".json"

        if os.environ.get("YAYBU_RECORD_FIXTURES", "") == "YES":
            context = self._setUp_for_recording()
        else:
            context = self._setUp_for_playback()

        self.Transport.path = self.path
        self.Transport.id = self.id()

        # Get a transport to inspect the changes Yaybu makes to a fakechroot
        self.transport = self.Transport(context, 5, False)

        # Let yaybu use this fakechroot
        from yaybu.provisioner import Provision
        Provision.transports["fakechroot"] = self.Transport
        #self.addCleanup(operator.del, Provision.transports, "fakechroot")

    def _setUp_for_recording(self):
        chroot = self.FakeChroot.create_in_tempdir(self.location)
        self.addCleanup(chroot.destroy)
        chroot.build()

        self.chroot_path = os.path.realpath(chroot.path)

        TransportRecorder.results = self.results = []

        def cleanup():
            existing = {}
            if os.path.exists(self.path):
                existing = json.load(open(self.path))
            existing[self.id()] = self.results
            with open(self.path, "w") as fp:
                json.dump(existing, fp)
        self.addCleanup(cleanup)

        self.Transport = TransportRecorder

        class FakeContext:
            host = "fakechroot://" + self.chroot_path

        return FakeContext()

    def _setUp_for_playback(self):
        t = self.Transport = TransportPlayback
        payload = pkgutil.get_data("yaybu.tests", os.path.basename(self.path))
        if payload:
            all_results = json.loads(payload)
        else:
            all_results = {}
        t.results = all_results.get(self.id(), [])

        self.chroot_path = "/tmp-playback-XOXOXO"

        return None

    def failUnlessExists(self, path):
        assert self.transport.exists(path), "%s doesnt exist" % path

    def failIfExists(self, path):
        assert not self.transport.exists(path), "%s does exist" % path

    def _config(self, contents):
        compute_stanza = textwrap.dedent("""
        #new FakeChroot as server:
        server:
            location: %s
            fqdn: fakechroot://{{ server.location }}
        """ % os.path.realpath(self.chroot_path))

        provisioner_stanza = textwrap.dedent("""
        new Provisioner as main:
            server: {{ server }}
            resources: {{ resources }}
        """)

        testcase_stanza = textwrap.dedent(contents)

        return super(TestCase, self)._config("\n\n".join((compute_stanza, provisioner_stanza, testcase_stanza)))

    # FIXME: Methods beyond this point are deprecated
    apply = BaseTestCase._up
    check_apply = BaseTestCase.up
