# Copyright 2013 Isotoma Limited
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


import os, signal

from yaybu.tests.provisioner_fixture import TestCase
from yaybu import error


simpleservice = """
#! /usr/bin/env python
import os, select, sys
if __name__ == "__main__":
    if os.fork() != 0:
        os._exit(0)

    os.setsid()

    if os.fork() != 0:
        os._exit(0)

    open("simple_daemon.pid", "w").write(str(os.getpid()))
    #os.chdir("/")
    os.umask(0)

    for fd in range(0, 1024):
        try:
            os.close(fd)
        except OSError:
            pass

    os.open("/dev/null", os.O_RDWR)

    os.dup2(0, 1)
    os.dup2(0, 2)

    while True:
        select.select([sys.stdin], [], [])
"""


class TestSimpleService(TestCase):

    def setUp(self):
        super(TestSimpleService, self).setUp()

        with self.chroot.open("/bin/simple_daemon", "w") as fp:
            fp.write(simpleservice)

    def test_start(self):
        self.chroot.check_apply("""
            resources:
                - Service:
                    name: test
                    policy: start
                    start: python /bin/simple_daemon
                    pidfile: /simple_daemon.pid
            """)

        with self.chroot.open("/simple_daemon.pid") as fp:
            pid = int(fp.read())

        os.kill(pid, signal.SIGTERM)

    def test_stop(self):
        self.chroot.call(["python", "/bin/simple_daemon"])

        self.chroot.check_apply("""
            resources:
                - Service:
                    name: test
                    policy: stop
                    stop: sh -c 'kill $(cat /simple_daemon.pid)'
                    pidfile: /simple_daemon.pid
            """)

    def test_restart(self):
        self.chroot.apply("""
            resources:
                - Service:
                    name: test
                    policy: restart
                    restart: touch /foo
            """)

        # We restart every time config is applied - so check_apply would fail the
        # automatic idempotentcy check
        self.failUnlessExists("/foo")

    def test_running_true(self):
        self.assertRaises(error.NothingChanged, self.chroot.apply, """
            resources:
                - Service:
                    name: test
                    start: touch /test_running_true
                    running: /bin/sh -c "true"
            """)

    def test_running_false(self):
        self.chroot.apply("""
            resources:
                - Service:
                    name: test
                    start: touch /test_running_false
                    running: /bin/sh -c "false"
            """)

        self.failUnlessExists("/test_running_false")

