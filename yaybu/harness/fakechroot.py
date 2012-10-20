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

import os, signal, shlex, subprocess, tempfile, time, shutil, StringIO
import testtools
from testtools.testcase import TestSkipped
from yaybu.core import error
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

# A little SSH wrapper for faking SSH into a fakechroot
# (Obviously won't let us fake paramiko...)
sshwrapper = """
#! /usr/bin/env python
import os, sys
args = sys.argv[1:]
while args and not args[0] == "yaybu":
    del args[0]
if args:
    os.execvp(args[0], args)
""".strip()

distro_flags = {
    "Ubuntu 9.10": dict(
        name="karmic",
        ),
    "Ubuntu 10.04": dict(
        name="lucid",
        ),
    "Ubuntu 10.10": dict(
        name="maverick",
        ),
    "Ubuntu 11.04": dict(
        name="natty",
        ),
    "Ubuntu 12.04": dict(
        name="precise",
        ),
   }

class FakeChrootFixture(Fixture):

    """
    I provide a very simple COW userspace environment in which to test configuration

    I am used for some of Yaybu's internal tests.
    """

    firstrun = True

    fakerootkey = None

    testbase = os.getenv("YAYBU_TESTS_BASE", "base-image")
    test_network = os.environ.get("TEST_NETWORK", "0") == "1"
    statefile = os.path.realpath("fakeroot.state")

    def setUp(self):
        try:
            self.sundayname = open("/etc/issue.net","r").read().strip()[:12]
        except:
            raise NotImplementedError("Can only run Integration tests on Ubuntu")
        if self.sundayname not in distro_flags:
            raise NotImplementedError("This version of Ubuntu (%r) is not supported" % self.sundayname)

        dependencies = (
            "/usr/bin/fakeroot",
            "/usr/bin/fakechroot",
            "/usr/sbin/debootstrap",
            "/usr/bin/cow-shell",
            )

        for dep in dependencies:
            if not os.path.exists(dep):
                raise NotImplementedError("Need '%s' to run integration tests" % dep)

        if self.firstrun:
            if not os.path.exists(self.testbase):
                self.build_environment()
            self.refresh_environment()

            # We only refresh the base environment once, so
            # set this on the class to make sure any other fixtures pick it up
            FakeChrootFixture.firstrun = False

        self.clone()

    def clone(self):
        self.chroot_path = os.path.realpath("tmp")
        subprocess.check_call(["cp", "-al", self.testbase, self.chroot_path])
        self.call(["/bin/true"], new_save_file=True)
        if os.path.islink(os.path.join(self.chroot_path, "var", "run")):
            os.unlink(os.path.join(self.chroot_path, "var", "run"))
            os.mkdir(os.path.join(self.chroot_path, "var", "run"))

        with self.open("/etc/yaybu", "w") as fp:
            fp.write(yaybu_cfg)
        self.chmod("/etc/yaybu", 0644)

    def cleanUp(self):
        subprocess.check_call(["rm", "-rf", self.chroot_path])

    def reset(self):
        self.cleanUp()
        self.clone()

    def distro(self):
        return distro_flags[self.sundayname]['name']
    
    def run_commands(self, commands, distro=None):
        for command in commands:
            command = command % dict(base_image=self.testbase, distro=distro)
            print ">>>", command
            p = subprocess.Popen(shlex.split(command))
            if p.wait():
                raise SystemExit("Command failed")
            
    def build_environment(self):
        distro = self.distro()
        commands = [
            "fakeroot fakechroot debootstrap --variant=fakechroot --include=git-core,python-setuptools,python-dateutil,python-magic,ubuntu-keyring,gpgv,python-dev,build-essential %(distro)s %(base_image)s",
            "fakeroot fakechroot /usr/sbin/chroot %(base_image)s apt-get update",
            ]
        if not os.path.exists(self.testbase):
            self.run_commands(commands, distro)

    def refresh_environment(self):
        commands = [
             "fakeroot fakechroot rm -rf /usr/local/lib/python2.6/dist-packages/Yaybu*",
             "fakeroot fakechroot rm -rf /usr/local/lib/python2.7/dist-packages/Yaybu*",
             "python setup.py sdist --dist-dir %(base_image)s",
             "fakeroot fakechroot /usr/sbin/chroot %(base_image)s sh -c 'easy_install /Yaybu-*.tar.gz'",
             ]
        self.run_commands(commands)

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
        return "/tmp/" + os.path.realpath(f.name).split("/")[-1]

    def call(self, command, new_save_file=False):
        env = os.environ.copy()
        env['HOME'] = '/root/'

        # Meh, we inherit the invoking users environment - LAME.
        env['HOME'] = '/root'
        env['PWD'] = '/'
        env['LOGNAME'] = 'root'
        env['USERNAME'] = 'root'
        env['USER'] = 'root'

        if new_save_file:
            chroot = ["fakeroot", "-s", self.statefile, "fakechroot", "cow-shell", "/usr/sbin/chroot", self.chroot_path]
        else:
            chroot = ["fakeroot", "-i", self.statefile, "-s", self.statefile, "fakechroot", "cow-shell", "/usr/sbin/chroot", self.chroot_path]
        print ">>>", " ".join(chroot+command)
        retval = subprocess.call(chroot + command, cwd=self.chroot_path, env=env)

        self.wait_for_cowdancer()
        return retval

    def yaybu(self, *args):
        filespath = os.path.join("/tmp", "files")
        args = list(args)
        if self.test_network:
            args.insert(0, "test://")
            args.insert(0, "--host")
            args.insert(0, "push")
        else:
            args.insert(0, "apply")

        return self.call(["yaybu", "-v", "-v", "-d", "--ypath", filespath] + args)

    def simulate(self, *args):
        """ Run yaybu in simulate mode """
        args = ["--simulate"] + list(args)
        return self.yaybu(*args)

    def apply(self, contents, *args):
        path = self.write_temporary_file(contents)
        return self.yaybu(path, *args)

    def apply_simulate(self, contents):
        path = self.write_temporary_file(contents)
        return self.simulate(path)

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

    def wait_for_cowdancer(self):
        # give cowdancer a few seconds to exit (avoids a race where it delets another sessions .ilist)
        for i in range(20):
            if not os.path.exists(os.path.join(self.chroot_path, ".ilist")):
                break
            time.sleep(0.1)

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
        return os.path.join(self.chroot_path, *path.split(os.path.sep))

    def get_user(self, user):
        users_list = open(self._enpathinate("/etc/passwd")).read().splitlines()
        users = dict(u.split(":", 1) for u in users_list)
        return users[user].split(":")

    def get_group(self, group):
        # Returns a tuple of group info if the group exists, or raises KeyError if it does not
        groups_list = open(self._enpathinate("/etc/group")).read().splitlines()
        groups = dict(g.split(":", 1) for g in groups_list)
        return groups[group].split(":")

