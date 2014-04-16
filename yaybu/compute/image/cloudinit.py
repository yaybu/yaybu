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
    args=["-output", "{pathname}", "-volid", "cidata", "-joliet", "-rock"],
    log_execution=True)


class CloudConfig:

    filename = "user-data"

    terms = [
        "package_upgrade",
        "package_update",
        "package_reboot_if_required",
        "packages",
        "runcmd",
    ]

    def __init__(self, auth, **kwargs):
        self.auth = auth

    def get_config(self):
        config = {}
        for t in self.terms:
            if hasattr(self, t):
                config[t] = getattr(self, t)
        if hasattr(self, 'auth'):
            if self.username and self.password:
                self.set_password_auth(config)
        return config

    @property
    def username(self):
        return getattr(self.auth, "username", None)

    @property
    def password(self):
        return getattr(self.auth, "password", None)

    @property
    def hashed_password(self):
        if self.password is None:
            return None
        return self.encrypt(self.password)

    def set_password_auth(self, config):
        if self.username != "ubuntu":
            logging.warn("A username other than 'ubuntu' is not supported on earlier versions of ubuntu")
        default_user = {
            "name": self.username,
            "passwd": self.hashed_password,
            "gecos": "Yaybu",
            "groups": ["adm", "audio", "cdrom", "dialout", "floppy", "video", "plugdev", "dip", "netdev"],
            "lock-passwd": False,
            "inactive": False,
            "system": False,
            "no-create-home": False,
            "sudo": "ALL=(ALL) NOPASSWD:ALL",
        }
        config['users'] = [default_user]
        config['ssh_pwauth'] = True
        config['chpasswd'] = {'expire': False}
        config['password'] = self.password

    def encrypt(self, passwd):
        """ Return the password hash for the specified password """
        salt = self.generate_salt()
        return crypt.crypt(passwd, "$5${0}$".format(salt))

    def generate_salt(self, length=16):
        salt_set = ('abcdefghijklmnopqrstuvwxyz'
                    'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
                    '0123456789./')
        return ''.join([random.choice(salt_set) for i in range(length)])

    def open(self):
        config = self.get_config()
        f = StringIO.StringIO()
        print >> f, "#cloud-config"
        print >> f, yaml.dump(config)
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

    seed_file_name = "seed.iso"

    def __init__(self, directory, cloud_config, meta_data, *files):
        self.cloud_config = cloud_config
        self.meta_data = meta_data
        self.directory = directory
        self.files = [self.cloud_config, self.meta_data]
        self.files.extend(files)
        self.tmpdir = tempfile.mkdtemp()

    @property
    def username(self):
        return self.cloud_config.username

    @property
    def password(self):
        return self.cloud_config.password

    @property
    def hashed_password(self):
        return self.cloud_config.hashed_password

    @property
    def pathname(self):
        return os.path.join(self.directory, self.seed_file_name)

    @property
    def filenames(self):
        for f in self.files:
            yield f.filename

    def _save(self):
        """ Overwrite the seed ISO file. Will clobber it potentially."""
        genisoimage(*self.filenames, pathname=self.pathname, cwd=self.tmpdir)

    def open(self, filename):
        path = os.path.join(self.tmpdir, filename)
        return open(path, "w")

    def _output(self, cloudfile):
        fout = self.open(cloudfile.filename)
        fin = cloudfile.open()
        fout.write(fin.read())

    def write(self):
        for f in self.files:
            self._output(f)
        self._save()
        self._cleanup()

    def _cleanup(self):
        for f in self.filenames:
            os.unlink(os.path.join(self.tmpdir, f))
        os.rmdir(self.tmpdir)
