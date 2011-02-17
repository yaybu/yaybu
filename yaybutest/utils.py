import os, shlex, subprocess, tempfile
import testtools

def run_commands(commands, base_image, distro='lucid'):
    for command in commands:
        command = command % dict(base_image=base_image, distro=distro)
        p = subprocess.Popen(shlex.split(command))
        if p.wait():
            raise SystemExit("Command failed")


def build_environment(base_image, distro='lucid'):
    commands = [
        "fakeroot fakechroot -s debootstrap --variant=fakechroot --include=python-setuptools,python-dateutil,ubuntu-keyring %(distro)s %(base_image)s",
        ]
    if not os.path.exists(base_image):
        run_commands(commands, base_image, distro)
    refresh_environment(base_image)

def refresh_environment(base_image):
    commands = [
        "rm -rf /usr/local/lib/python2.6/dist-packages/Yaybu*",
        "python setup.py sdist --dist-dir %(base_image)s",
        "fakeroot fakechroot -s chroot %(base_image)s sh -c 'easy_install /Yaybu-*.tar.gz'",
        ]
    run_commands(commands, base_image)


class TestCase(testtools.TestCase):

    def write_temporary_file(self, contents):
        f = tempfile.NamedTemporaryFile(dir=os.path.join(self.chroot_path, 'tmp'), delete=False)
        f.write(contents)
        f.close()
        return f.name

    def call(self, command):
        chroot = ["fakeroot", "fakechroot", "-s", "cow-shell", "chroot", self.chroot_path]
        subprocess.check_call(chroot + command, cwd=self.chroot_path)

    def yaybu(self, *args):
        self.call(["yaybu"] + list(args))

    def apply(self, contents):
        path = self.write_temporary_file(contents)
        self.yaybu(path)

    def setUp(self):
        super(TestCase, self).setUp()
        self.chroot_path = os.path.realpath("tmp")
        subprocess.check_call(["cp", "-al", os.getenv("YAYBU_TESTS_BASE"), self.chroot_path])

    def tearDown(self):
        super(TestCase, self).tearDown()
        subprocess.check_call(["rm", "-rf", self.chroot_path])

    def failUnlessExists(self, path):
        full_path = os.path.join(self.chroot_path, *path.split(os.path.sep))
        self.failUnless(os.path.exists(full_path))
