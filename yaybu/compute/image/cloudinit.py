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
import subprocess
import logging

from . import error

logger = logging.getLogger("cloudinit")


class Seed:

    filenames = ['meta-data', 'user-data']

    def __init__(self, seedfile):
        self.seedfile = os.path.realpath(seedfile)
        self.tmpdir = tempfile.mkdtemp()

    def save(self):
        """ Overwrite the seed ISO file. Will clobber it potentially."""
        command = [
            "genisoimage",
            "-output", self.seedfile,
            "-volid", "cidata",
            "-joliet", "-rock",
        ]
        command.extend(self.filenames)
        p = subprocess.Popen(
            args=command,
            stdin=None,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=self.tmpdir
        )
        stdout, stderr = p.communicate()
        if p.returncode != 0:
            raise error.CloudInitException("genisoimage failed", log=stdout + stderr)

    def open(self, filename, mode):
        path = os.path.join(self.tmpdir, filename)
        return open(path, mode)

    def create_meta_data(self):
        f = self.open("meta-data", "w")
        print >> f, "local-hostname: localhost"
        print >> f, "instance-id: foo1"

    def create_user_data(self):
        f = self.open("user-data", "w")
        print >> f, "#cloud-config"
        print >> f, "password: password"
        print >> f, "chpasswd: { expire: False }"

    def update(self):
        for f in self.filenames:
            fn = "create_" + f.replace("-", "_")
            getattr(self, fn)()
        self.save()

    def cleanup(self):
        for f in self.filenames:
            os.unlink(os.path.join(self.tmpdir, f))
        os.rmdir(self.tmpdir)
