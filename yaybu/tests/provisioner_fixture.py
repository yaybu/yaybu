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
import operator
import tempfile
import urlparse
import urllib

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
from yaybu import error
from yaybu.tests.base import TestCase as BaseTestCase
from yaybu.provisioner.transports.remote import stat_result, \
    struct_group, struct_passwd, struct_spwd
from yaybu.provisioner.transports.fakechroot import FakechrootTransport


class TransportRecorder(object):

    def __init__(self, context, *args, **kwargs):
        q = urlparse.urlparse(context.host)
        self.path = q.path
        qs = urlparse.parse_qs(q.query)
        self.id = qs['id'][0]

        # Set up the backend to record
        target = context.params.target.fqdn.as_string()
        bq = urlparse.urlparse(target)
        Transport = context.transports[bq.scheme]
        context.host = target
        self.inner = Transport(context, *args, **kwargs)

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

    def __init__(self, context, *args, **kwargs):
        q = urlparse.urlparse(context.host)
        self.path = q.path
        qs = urlparse.parse_qs(q.query)
        self.id = qs['id'][0]
        context.host = context.params.target.fqdn.as_string()

        if not self.results:
            payload = pkgutil.get_data("yaybu.tests", os.path.basename(self.path))
            if payload:
                all_results = json.loads(payload)
            else:
                all_results = {}
            self.results.extend(all_results.get(self.id, []))

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
        self.members['fqdn'] = "fakechroot://" + location

        if self.root.readonly or self.root.simulate:
            return

        if not os.path.exists(os.path.join(location, "chroot")):
            FakeChroot(location).build()
            self.root.changed()

    def destroy(self):
        location = self.params.location.as_string()
        FakeChroot(location).destroy()

    @classmethod
    def install(cls, testcase):
        from yaybu.core.config import Config
        Config.default_builtins["FakeChroot"] = cls
        testcase.addCleanup(operator.delitem, Config.default_builtins, "FakeChroot")


class TestCase(BaseTestCase):

    location = os.path.join(os.path.dirname(__file__), "..", "..", "..")

    def setUp(self):
        self.path = inspect.getfile(self.__class__).rsplit(".", 1)[0] + ".json"
        self.uri = "?".join((self.path, urllib.urlencode({"id": self.id()})))

        # Setup the provisioner transports used for testing
        transports = [
            ("fakechroot", FakechrootTransport),
            ("record", TransportRecorder),
            ("playback", TransportPlayback),
        ]

        from yaybu.provisioner import Provision
        for name, transport in transports:
            Provision.transports[name] = transport
            self.addCleanup(operator.delitem, Provision.transports, name)

        FakeChrootPart.install(self)

        # Yuck - the transport instances have shared state!
        self.results = TransportRecorder.results = TransportPlayback.results = []

        if os.environ.get("YAYBU_RECORD_FIXTURES", "") == "YES":
            context = self._setUp_for_recording()
        else:
            context = self._setUp_for_playback()

        try:
            self._up("resources: []")
        except error.NothingChanged:
            pass

        self.addCleanup(self.destroy, "resources: []")

        # FIXME: Nicer API here perhaps?
        provisioner = self._get_graph("resources: []").main.expand()
        provisioner.apply()
        self.transport = provisioner.transport

    def _setUp_for_recording(self):
        self.chroot_path = tempfile.mkdtemp(dir=os.path.abspath(self.location))

        self.compute_stanza = textwrap.dedent("""
            new FakeChroot as server:
                location: %s
        """ % os.path.realpath(self.chroot_path))

        self.provisioner_stanza = textwrap.dedent("""
            new Provisioner as main:
              server:
                  fqdn: record://%s
              target: {{ server }}
              resources: {{ resources }}
        """ % self.uri)

        def cleanup():
            existing = {}
            if os.path.exists(self.path):
                existing = json.load(open(self.path))
            existing[self.id()] = self.results
            with open(self.path, "w") as fp:
                json.dump(existing, fp)
        self.addCleanup(cleanup)

        class FakeContext:
            host = "fakechroot://" + self.chroot_path

        return FakeContext()

    def _setUp_for_playback(self):
        self.chroot_path = "/tmp-playback-XOXOXO"

        self.compute_stanza = textwrap.dedent("""
            server:
                fqdn: fakechroot://%s
        """ % os.path.realpath(self.chroot_path))

        self.provisioner_stanza = textwrap.dedent("""
            new Provisioner as main:
              server:
                  fqdn: playback://%s
              target: {{ server }}
              resources: {{ resources }}
        """ % self.uri)

        return None

    def failUnlessExists(self, path):
        assert self.transport.exists(path), "%s doesnt exist" % path

    def failIfExists(self, path):
        assert not self.transport.exists(path), "%s does exist" % path

    def _config(self, contents):
        testcase_stanza = textwrap.dedent(contents)
        return super(TestCase, self)._config("\n\n".join((
            self.compute_stanza,
            self.provisioner_stanza,
            testcase_stanza
        )))

    # FIXME: Methods beyond this point are deprecated
    apply = BaseTestCase._up
    check_apply = BaseTestCase.up
