import os, shutil, grp, signal

from yaybutest.utils import TestCase
from yaybu.util import sibpath


class TestSimpleService(TestCase):

    def test_start(self):
        src = sibpath(__file__, os.path.join("..", "..", "files"))
        dst = os.path.join(self.chroot_path, "tmp", "files")
        shutil.copytree(src, dst)

        self.check_apply("""
            resources:
                - Service:
                    name: test
                    policy: start
                    start: python /tmp/files/simple_daemon
                    pidfile: /simple_daemon.pid
            """)

        os.kill(int(open(self.enpathinate("/simple_daemon.pid")).read()), signal.SIGTERM)

    def test_stop(self):
        src = sibpath(__file__, os.path.join("..", "..", "files"))
        dst = os.path.join(self.chroot_path, "tmp", "files")
        shutil.copytree(src, dst)

        self.call(["python", "/tmp/files/simple_daemon"])

        self.check_apply("""
            resources:
                - Service:
                    name: test
                    policy: stop
                    stop: sh -c 'kill $(cat /simple_daemon.pid)'
                    pidfile: /simple_daemon.pid
            """)

    def test_restart(self):
        rv = self.apply("""
            resources:
                - Service:
                    name: test
                    policy: restart
                    restart: touch /foo
            """)

        # We restart every time config is applied - so check_apply would fail the
        # automatic idempotentcy check
        self.failUnlessEqual(rv, 0)
        self.failUnlessExists("/foo")
