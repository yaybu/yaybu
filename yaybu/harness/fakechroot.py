# Copyright 2011 Isotoma Limited
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

import os, sys, glob, signal, shlex, subprocess, tempfile, time, shutil, StringIO
from unittest2 import SkipTest
from yaybu import error
from yaybu.util import sibpath

from yaybu.harness.fixture import Fixture

# Setup environment passthrough for chroot environment
# And turn on auditlog
yaybu_cfg = """
env-passthrough:
 - COWDANCER_ILISTFILE
 - FAKECHROOT
 - FAKECHROOT_VERSION
 - FAKECHROOT_BASE
 - FAKED_MODE
 - FAKEROOTKEY
 - LD_PRELOAD
 - LD_LIBRARY_PATH
auditlog:
   mode: file
"""

distro_flags = {
    "Ubuntu 10.04": dict(
        name="lucid",
        ),
    "Ubuntu 12.04": dict(
        name="precise",
        ),
    "Ubuntu 12.10": dict(
        name="quantal",
    )
   }


class FakeChrootFixture(Fixture):

    """
    I provide a very simple COW userspace environment in which to test configuration

    I am used for some of Yaybu's internal tests.
    """

    firstrun = True
    sundayname = "unknown"
    fakerootkey = None
    faked = None

    testbase = os.path.realpath(os.getenv("YAYBU_TESTS_BASE", "base-image"))
    statefile = os.path.realpath("fakeroot.state")

    def setUp(self):
        try:
            self.sundayname = open("/etc/issue.net","r").read().strip()[:12]
        except:
            raise SkipTest("Can only run Integration tests on Ubuntu")

        if self.sundayname not in distro_flags:
            raise SkipTest("This version of Ubuntu (%r) is not supported" % self.sundayname)

        dependencies = (
            "/usr/bin/fakeroot",
            "/usr/bin/fakechroot",
            "/usr/sbin/debootstrap",
            "/usr/bin/cow-shell",
            )

        for dep in dependencies:
            if not os.path.exists(dep):
                raise SkipTest("Need '%s' to run integration tests" % dep)

        if not os.path.exists(self.testbase):
            self.build_environment()

        self.clone()

    def clone(self):
        self.chroot_path = os.path.realpath("tmp")
        self.ilist_path = self.chroot_path + ".ilist"

        subprocess.check_call(["cp", "-al", self.testbase, self.chroot_path])

        # This is the same delightful incantation used in cow-shell to setup an
        # .ilist file for our fakechroot.
        subprocess.check_call([
            "cowdancer-ilistcreate",
            self.ilist_path,
            "find . -xdev \( -type l -o -type f \) -a -links +1 -print0 | xargs -0 stat --format '%d %i '",
            ], cwd=self.chroot_path)

        # On newer installations /var/run is now a symlink to /run
        # This breaks our fakechrootage so don't do it
        if os.path.islink(os.path.join(self.chroot_path, "var", "run")):
            os.unlink(os.path.join(self.chroot_path, "var", "run"))
            os.mkdir(os.path.join(self.chroot_path, "var", "run"))

        # mkdir was needed by Doug on Quantal - but blows up on Lucid and
        # Precise - so added exists guard
        if not os.path.exists(os.path.join(self.chroot_path, "etc")):
            os.mkdir(os.path.join(self.chroot_path, "etc"))
        if not os.path.exists(os.path.join(self.chroot_path, "tmp")):
            os.mkdir(os.path.join(self.chroot_path, "tmp"))

        with self.open("/etc/yaybu", "w") as fp:
            fp.write(yaybu_cfg)

    def cleanUp(self):
        self.cleanup_session()
        if os.path.exists(self.ilist_path):
            os.unlink(self.ilist_path)
        subprocess.check_call(["rm", "-rf", self.chroot_path])

    def reset(self):
        self.cleanUp()
        self.clone()

    def distro(self):
        return distro_flags[self.sundayname]['name']

    def msg(self, *msg):
        sys.__stdout__.write("%s\n" % " ".join(msg))
        sys.__stdout__.flush()

    def run_command(self, command, distro=None, cwd=None):
        command = command % dict(base_image=self.testbase, distro=distro)
        self.msg(">>>", command)
        p = subprocess.Popen(shlex.split(command), cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        p.communicate()
        if p.returncode:
            raise SystemExit("Command failed")

    def build_environment(self):
        if os.path.exists(self.testbase):
            return

        self.msg("Need to create a base fakechroot! This might take some time...")

        distro = self.distro()
        commands = [
            "fakeroot fakechroot debootstrap --variant=fakechroot --include=sudo,git-core,python-setuptools,ubuntu-keyring,gpgv,build-essential %(distro)s %(base_image)s",
            "fakeroot fakechroot /usr/sbin/chroot %(base_image)s apt-get update",
            ]
        for command in commands:
            self.run_command(command, distro)

    def cleanup_session(self):
        if self.faked:
            os.kill(int(self.faked.strip()), signal.SIGTERM)
            self.faked = None

    def get_session(self):
        if self.fakerootkey:
            return self.fakerootkey

        p = subprocess.Popen(['faked-sysv'], stdout=subprocess.PIPE)

        stdout, stderr = p.communicate()
        self.fakerootkey, self.faked = stdout.split(":")
        return self.fakerootkey

    def write_temporary_file(self, contents):
        f = tempfile.NamedTemporaryFile(dir=os.path.join(self.chroot_path, 'tmp'), delete=False)
        f.write(contents)
        f.close()
        return f.name, "/tmp/" + os.path.realpath(f.name).split("/")[-1]

    def get_env(self):
        env = {}

        path = os.path.realpath(os.path.join(self.chroot_path, ".."))

        env['FAKECHROOT'] = 'true'
        env['FAKECHROOT_EXCLUDE_PATH'] = ":".join([
            '/dev', '/proc', '/sys', path,
            ])
        env['FAKECHROOT_CMD_SUBST'] = ":".join([
            '/usr/sbin/chroot=/usr/sbin/chroot.fakechroot',
            '/sbin/ldconfig=/bin/true',
            '/usr/bin/ischroot=/bin/true',
            '/usr/bin/ldd=/usr/bin/ldd.fakechroot',
            '/usr/bin/sudo=%s' % os.path.join(path, "testing", "sudo"),
            '/usr/bin/env=%s' % os.path.join(path, "testing", "env"),
            ])
        env['FAKECHROOT_BASE'] = self.chroot_path

        if "FAKECHROOT_DEBUG" in os.environ:
            env['FAKECHROOT_DEBUG'] = 'true'

        # Set up fakeroot stuff
        env['FAKEROOTKEY'] = self.get_session()

        # Cowdancer stuff
        env['COWDANCER_ILISTFILE'] = self.ilist_path
        env['COWDANCER_REUSE'] = 'yes'

        # Meh, we inherit the invoking users environment - LAME.
        env['HOME'] = '/root'
        env['PWD'] = '/'
        env['LOGNAME'] = 'root'
        env['USERNAME'] = 'root'
        env['USER'] = 'root'

        LD_LIBRARY_PATH = []
        for path in ("/usr/lib/fakechroot", "/usr/lib64/fakechroot", "/usr/lib32/fakechroot", ):
            if os.path.exists(path):
                LD_LIBRARY_PATH.append(path)
        LD_LIBRARY_PATH.extend(glob.glob("/usr/lib/*/fakechroot"))

        for path in ("/usr/lib/libfakeroot", ):
            if os.path.exists(path):
                LD_LIBRARY_PATH.append(path)
        LD_LIBRARY_PATH.extend(glob.glob("/usr/lib/*/libfakeroot"))

        # Whether or not to use system libs depends on te presence of the next line
        if True:
            LD_LIBRARY_PATH.append("/usr/lib")
            LD_LIBRARY_PATH.append("/lib")

        LD_LIBRARY_PATH.append(os.path.join(self.chroot_path, "usr", "lib"))
        LD_LIBRARY_PATH.append(os.path.join(self.chroot_path, "lib"))

        env['LD_LIBRARY_PATH'] = ":".join(LD_LIBRARY_PATH)
        env['LD_PRELOAD'] = "libfakechroot.so libfakeroot-sysv.so /usr/lib/cowdancer/libcowdancer.so"
        return env

    def call(self, command):
        env = self.get_env()
        p = subprocess.Popen(command, cwd=self.chroot_path, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        stdout, stderr = p.communicate()
        print stdout
        return p.returncode

    def yaybu(self, *args):
        from yaybu.core import event
        event.reset(True)
       
        from yaybu.parts.provisioner.transports import FakechrootTransport
        FakechrootTransport.env = self.get_env()
        FakechrootTransport.chroot_path = self.chroot_path

        from yaybu.parts import Provision
        Provision.Transport = FakechrootTransport

        filespath = os.path.join(self.chroot_path, "/tmp", "files")
        from yaybu.core.command import YaybuCmd
        from optparse import OptionParser

        p = OptionParser()
        y = YaybuCmd(ypath=(filespath, ))
        y.ypath = [filespath]
        y.verbose = 2
        y.debug = True
        y.opts_up(p)
        try:
            return y.do_up(*p.parse_args(list(args)))
        except SystemError:
            return 0

    def simulate(self, *args):
        """ Run yaybu in simulate mode """
        args = ["--simulate"] + list(args)
        return self.yaybu(*args)

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

        return self.yaybu("-C", path2, *args)

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

        return self.simulate("-C", path2)

    def check_apply(self, contents, *args, **kwargs):
        expect = kwargs.get('expect', 0)

        # Apply the change in simulate mode
        sim_args = list(args) + ["-s"]
        rv = self.apply(contents, *sim_args)
        if rv != expect:
            raise subprocess.CalledProcessError(rv, "Simulation failed: got rv %s" % rv)

        # Apply the change for real
        rv = self.apply(contents, *args)
        if rv != expect:
            raise subprocess.CalledProcessError(rv, "Apply failed: got rv %s" % rv)

        # If 'expect' isnt 0 then theres no point doing a no-changes check
        if expect != 0:
            return

        # If we apply the change again nothing should be changed
        rv = self.apply(contents, *args)
        if rv != error.NothingChanged.returncode:
            raise subprocess.CalledProcessError(rv, "Change still outstanding")

    def check_apply_simulate(self, contents):
        rv = self.apply_simulate(contents)
        if rv != 0:
            raise subprocess.CalledProcessError(rv, "Simulate failed rv %s" % rv)

    def exists(self, path):
        return os.path.exists(self._enpathinate(path))

    def isdir(self, path):
        return os.path.isdir(self._enpathinate(path))

    def mkdir(self, path):
        os.mkdir(self._enpathinate(path))

    def open(self, path, mode='r'):
        return open(self._enpathinate(path), mode)

    def touch(self, path):
        if not self.exists(path):
            with self.open(path, "w") as fp:
                fp.write("")

    def chmod(self, path, mode):
        self.call(["chmod", "%04o" % mode, path])

    def readlink(self, path):
        relpath = os.path.relpath(os.readlink(self._enpathinate(path)), self.chroot_path)
        for x in (".", "/"):
            if relpath.startswith(x):
                relpath = relpath[1:]
        return "/" + relpath

    def symlink(self, source, dest):
        os.symlink(self._enpathinate(source), self._enpathinate(dest))

    def stat(self, path):
        return os.stat(self._enpathinate(path))

    def _enpathinate(self, path):
        path = os.path.join(self.chroot_path, path.lstrip('/'))
        return path

    def get_user(self, user):
        users_list = open(self._enpathinate("/etc/passwd")).read().splitlines()
        users = dict(u.split(":", 1) for u in users_list)
        return users[user].split(":")

    def get_group(self, group):
        # Returns a tuple of group info if the group exists, or raises KeyError if it does not
        groups_list = open(self._enpathinate("/etc/group")).read().splitlines()
        groups = dict(g.split(":", 1) for g in groups_list)
        return groups[group].split(":")

