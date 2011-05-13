import os, shlex, subprocess, tempfile, time
import testtools

def default_distro():
    options = {
        "Ubuntu 9.10": "karmic",
        "Ubuntu 10.04": "lucid",
        "Ubuntu 10.10": "maverick",
        "Ubuntu 11.04": "natty",
        }
    sundayname = open("/etc/issue.net","r").read().strip()
    return options[sundayname[:12]]

def run_commands(commands, base_image, distro=None):
    for command in commands:
        command = command % dict(base_image=base_image, distro=distro)
        p = subprocess.Popen(shlex.split(command))
        if p.wait():
            raise SystemExit("Command failed")


def build_environment(base_image):
    distro = default_distro()
    commands = [
        "fakeroot fakechroot -s debootstrap --variant=fakechroot --include=python-setuptools,python-dateutil,python-magic,ubuntu-keyring,gpgv %(distro)s %(base_image)s",
        "fakeroot fakechroot -s chroot %(base_image)s apt-get update",
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
        retval = subprocess.call(chroot + command, cwd=self.chroot_path)
        self.wait_for_cowdancer()
        return retval

    def yaybu(self, *args):
        filespath = os.path.join(self.chroot_path, "tmp", "files")
        return self.call(["yaybu", "-d", "--ypath", filespath] + list(args))

    def simulate(self, *args):
        """ Run yaybu in simulate mode """
        filespath = os.path.join(self.chroot_path, "tmp", "files")
        return self.call(["yaybu", "--simulate", "--ypath", filespath] + list(args))

    def apply(self, contents, *args):
        path = self.write_temporary_file(contents)
        return self.yaybu(path, *args)

    def apply_simulate(self, contents):
        path = self.write_temporary_file(contents)
        return self.simulate(path)

    def check_apply(self, contents, *args):
        rv = self.apply(contents, *args)
        if rv != 0:
            raise subprocess.CalledProcessError(rv, "yaybu")

    def check_apply_simulate(self, contents):
        rv = self.apply_simulate(contents)
        if rv != 0:
            raise subprocess.CalledProcessError(rv, "yaybu")

    def wait_for_cowdancer(self):
        # give cowdancer a few seconds to exit (avoids a race where it delets another sessions .ilist)
        for i in range(20):
            if not os.path.exists(os.path.join(self.chroot_path, ".ilist")):
                break
            time.sleep(0.1)

    def setUp(self):
        super(TestCase, self).setUp()
        self.chroot_path = os.path.realpath("tmp")
        subprocess.check_call(["cp", "-al", os.getenv("YAYBU_TESTS_BASE"), self.chroot_path])

    def tearDown(self):
        super(TestCase, self).tearDown()

        subprocess.check_call(["rm", "-rf", self.chroot_path])

    def failUnlessExists(self, path):
        full_path = self.enpathinate(path)
        self.failUnless(os.path.exists(full_path))

    def enpathinate(self, path):
        return os.path.join(self.chroot_path, *path.split(os.path.sep))

    def get_user(self, user):
        users_list = open(self.enpathinate("/etc/passwd")).read().splitlines()
        users = dict(u.split(":", 1) for u in users_list)
        return users[user].split(":")

    def get_group(self, group):
        # Returns a tuple of group info if the group exists, or raises KeyError if it does not
        groups_list = open(self.enpathinate("/etc/group")).read().splitlines()
        groups = dict(g.split(":", 1) for g in groups_list)
        return groups[group].split(":")
