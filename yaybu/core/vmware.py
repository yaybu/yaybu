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

from __future__ import division
import time
import os.path
import urllib2
import hashlib
import tarfile
import subprocess

class VMException(Exception):
    pass

class VMSetup:

    def __init__(self, args):
        self.args = args

    @property
    def pubkey(self):
        return os.path.expanduser(self.args.pubkey)

    @property
    def vmdir(self):
        return os.path.expanduser(self.args.vmdir)

    @property
    def vmx(self):
        path = self.template_path
        return os.path.join(path, os.path.basename(path) + ".vmx")

    @property
    def template_path(self):
        return os.path.join(self.vmdir, self.args.vmname)

    @property
    def template_exists(self):
        return os.path.exists(self.template_path)

    @property
    def cache_path(self):
        return os.path.expanduser(self.args.filecache)

    @property
    def cache_exists(self):
        return os.path.exists(self.cache_path)

    @property
    def image(self):
        return self.args.image

    def run(self, command):
        return getattr(self, "command_" + command.replace("-", "_"))()

    def _vmrun(self, cmd, *args, **kwargs):
        def _k():
            for k, v in kwargs.items():
                yield "-" + k
                yield v
        command = ['vmrun'] + list(_k()) + [cmd, self.vmx] + list(args)
        print "Executing", command
        p = subprocess.Popen(command, stdin=None, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()
        if p.returncode != 0:
            print "Return code", p.returncode
            print "stdout:", stdout
            print "stderr:", stderr
        return stdout

    def vmrun(self, cmd, *args):
        return self._vmrun(cmd, *args, gu=self.args.vmuser, gp=self.args.vmpass)

    def command_install(self):
        if self.template_exists:
            print "Template already exists at", self.template_path, "nothing to do"
        else:
            if self.cache_exists:
                print "Cached copy exists, checking md5..."
                m = hashlib.md5()
                m.update(open(self.cache_path).read())
                md5 = m.hexdigest()
                remote_md5 = urllib2.urlopen(self.image + ".md5").read().strip()
                if md5 == remote_md5:
                    print "MD5 matches, not downloading"
                else:
                    print "MD5 does not match, downloading new copy", md5, remote_md5
                    self.download()
            else:
                self.download()
            self.extract()
            self.install_key()

    def command_install_key(self):
            self.install_key()


    def download(self):
        """ Download the image from the remote location and place it in the cache location """
        downloaded = 0
        batch_size = 8192
        percent = 0
        try:
            fout = open(self.cache_path, "w")
        except Exception, e:
            print "Unable to write to cache file", self.args.filecache
            raise
        try:
            start = time.time()
            fin = urllib2.urlopen(self.image)
            content_length = int(fin.headers['content-length'])
            print "Downloading image of size %dMb..." % (content_length/1024/1024)
            while True:
                data = fin.read(batch_size)
                if not data: break
                fout.write(data)
                downloaded += batch_size
                percent = downloaded / content_length * 100
                elapsed = time.time() - start
                bps = downloaded / elapsed
                if bps > (1024*1024):
                    speed = "%.02fMB/s" % (bps/1024/1024)
                elif bps > 1024:
                    speed = "%.02fKB/s" % (bps/1024)
                else:
                    speed = "%.02fB/s" % bps
                print "\r%2.02f%% (%s)                            " % (percent, speed),
        except urllib2.HTTPError, e:
            print "HTTP Error:", e.code, url
        except urllib2.URLError, e:
            print "URL Error:", e.reason, url
        fin.close()
        fout.close()

    def extract(self):
        print "Extracting..."
        t = tarfile.open(self.cache_path, "r:bz2")
        t.extractall(self.vmdir)

    def install_key(self):
        if not os.path.exists(self.pubkey):
            print "Your public key file", self.pubkey, "does not exist"
            raise SystemExit
        print "Starting template VM..."
        self.vmrun("start")
        stdout = self.vmrun("readVariable", "guestVar", "ip")
        ip = stdout.strip()
        self.vmrun("createDirectoryInGuest", "/home/ubuntu/.ssh")
        self.vmrun("copyFileFromHostToGuest", os.path.expanduser(self.args.pubkey), "/home/ubuntu/.ssh/authorized_keys")
        self.vmrun("runProgramInGuest", "/bin/chmod", "0700", "/home/ubuntu/.ssh")
        self.vmrun("runProgramInGuest", "/bin/chmod", "0600", "/home/ubuntu/.ssh/authorized_keys")
        self.vmrun("runProgramInGuest", "/usr/bin/sudo", "/sbin/shutdown", "-h", "now")

