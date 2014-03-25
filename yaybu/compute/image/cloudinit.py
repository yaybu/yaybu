# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import tempfile
import logging
import StringIO
import yaml
import random
import crypt

from yaybu.compute.util import SubRunner

logger = logging.getLogger("cloudinit")

genisoimage = SubRunner(
    command_name="genisoimage",
    args=["-output", "{seedfile}",
          "-volid", "cidata",
          "-joliet", "-rock"],
    log_execution=True,
)

vmware_tools_install = [
    ['mount', '/dev/sr1', '/mnt'],
    ['bash', '/mnt/run_upgrader.sh'],
    ['umount', '/mnt'],
]

# there is probably a neater way of doing this
open_tools_install = [
    ['sed', '-i', "'/^# deb.*multiverse/ s/^# //'", '/etc/apt/sources.list'],
    ['apt-get', 'update'],
    ['apt-get', 'install', '-y', 'open-vm-tools'],
]


class CloudConfig:

    filename = "user-data"

    config_modules = [
        "disk-setup",
        "mounts",
        "users_groups",
        "ssh-import-id",
        "locale",
        "set-passwords",
        "grub-dpkg",
        "apt-pipelining",
        "apt-update-upgrade",
        "timezone",
        "disable-ec2-metadata",
        "runcmd",
        "byobu",
    ]

    def __init__(self, auth, runcmd=None, apt_upgrade=False):
        self.config = {
            "apt_upgrade": apt_upgrade,
            "cloud_config_modules": self.config_modules,
        }
        if runcmd is not None:
            self.config['runcmd'] = runcmd
        if hasattr(auth, "password"):
            self.set_password_auth(auth.username, auth.password)

    def set_password_auth(self, username, password):
        if username != "ubuntu":
            logging.warn("A username other than 'ubuntu' is not supported on earlier versions of ubuntu")
        default_user = {
            "name": username,
            "passwd": self.encrypt(password),
            "gecos": "Yaybu",
            "groups": ["adm", "audio", "cdrom", "dialout", "floppy", "video", "plugdev", "dip", "netdev"],
            "lock-passwd": False,
            "inactive": False,
            "system": False,
            "sudo": "ALL=(ALL) NOPASSWD:ALL",
        }
        self.config['users'] = [default_user]
        self.config['ssh_pwauth'] = True
        self.config['chpasswd'] = {'expire': False}
        self.config['password'] = password

    def encrypt(self, passwd):
        """ Return the password hash for the specified password """
        salt = self.generate_salt()
        return crypt.crypt(passwd, "$5${0}$".format(salt))

    def generate_salt(self, length=16):
        salt_set = ('abcdefghijklmnopqrstuvwxyz'
                    'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
                    '0123456789./')
        return ''.join([random.choice(salt_set) for i in range(length)])

    def as_dict(self):
        return self.config

    def open(self):
        f = StringIO.StringIO()
        print >> f, "#cloud-config"
        print >> f, yaml.dump(self.config)
        return StringIO.StringIO(f.getvalue())


class MetaData:

    filename = "meta-data"

    def __init__(self, instance_id, localhost="localhost"):
        self.instance_id = instance_id
        self.localhost = localhost

    def as_dict(self):
        return {
            "local-hostname": self.localhost,
            "instance-id": self.instance_id,
        }

    def open(self):
        return StringIO.StringIO(yaml.dump(self.as_dict()))


class Seed:

    def __init__(self, seedfile, config_files):
        self.seedfile = seedfile
        self.files = config_files
        self.tmpdir = tempfile.mkdtemp()

    @property
    def filenames(self):
        for f in self.files:
            yield f.filename

    def _save(self):
        """ Overwrite the seed ISO file. Will clobber it potentially."""
        genisoimage(*self.filenames, seedfile=self.seedfile, cwd=self.tmpdir)

    def open(self, filename):
        path = os.path.join(self.tmpdir, filename)
        return open(path, "w")

    def _output(self, cloudfile):
        fout = self.open(cloudfile.filename)
        fin = cloudfile.open()
        fout.write(fin.read())

    def create(self):
        for f in self.files:
            self._output(f)
        self._save()
        self._cleanup()

    def _cleanup(self):
        for f in self.filenames:
            os.unlink(os.path.join(self.tmpdir, f))
        os.rmdir(self.tmpdir)
