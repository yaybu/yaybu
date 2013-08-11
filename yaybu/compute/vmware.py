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

# This driver presents a libcloud interface around vmrun - the command line API
# for controlling VMWare VM's.

# Base image notes:
#1. Install vmware tools from packages.vmware.com/tools - the latest esx ones work with vmware fusion
#2. Don't forget to delete the persistent net rules
#3. There needs to be a user with a password/key that can get to root without sudo requiring a passphrase.

#============================================================================================
# libcloud/common/proces.py

import os
import shlex
import subprocess
from pipes import quote

from libcloud.common.types import LibcloudError
import logging
import json
import urllib2
import uuid
import datetime
import urlparse

import zipfile

logger = logging.getLogger("yaybu.parts.compute.vmware")

class Response(object):

    def __init__(self, status, body, error):
        self.status = status
        self.body = body
        self.error = error

        if not self.success():
            raise LibcloudError(self.parse_error())

        self.object = self.parse_body()

    def parse_body(self):
        return self.body

    def parse_error(self):
        return self.error

    def success(self):
        return self.status == 0


class Connection(object):

    responseCls = Response
    log = None

    def  __init__(self, secure=True, host=None, port=None, url=None,
                  timeout=None):
        pass

    def connect(self):
        pass

    def request(self, command, data='', capture_output=True):
        if not isinstance(command, list):
            command = shlex.split(command)

        if self.log:
            self.log.write(' '.join(quote(c) for c in command) + '\n')

        if not capture_output:
            stdout, stderr = '', ''
            returncode = self._silent_request(command, data)
        else:
            returncode, stdout, stderr = self._request(command, data)

        if self.log:
            self.log.write("# returncode is %d\n" % returncode)
            self.log.write("# -------- begin stdout ----------\n")
            self.log.write(stdout)
            self.log.write("# -------- begin stderr ----------\n")
            self.log.write(stderr)
            self.log.write("# -------- end ----------\n")

        return self.responseCls(returncode, stdout, stderr)

    def _request(self, command, data):
        stdin = subprocess.PIPE if data else None
        p = subprocess.Popen(command, stdin=stdin, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = p.communicate(data)
        return p.returncode, stdout, stderr

    def _silent_request(self, command, data):
        stdin = subprocess.PIPE if data else None
        with open(os.devnull, "w") as null:
            p = subprocess.Popen(command, stdin=stdin, stdout=null, stderr=null)
            if data:
                p.stdin.write(data)
                p.stdin.close()
            return p.wait()

#=========================================================================================================

import os
import glob
import logging
import shutil
import uuid
import hashlib

from libcloud.common.types import LibcloudError
from libcloud.compute.base import NodeDriver, Node, NodeSize, NodeImage
from libcloud.compute.base import NodeState
from libcloud.compute.types import Provider

# FIXME:
Provider.VMWARE = 99

class VMXFile(object):

    def __init__(self, path):
        self.path = path
        self.settings = {}
        self.load()

    def load(self):
        self.settings = {}
        with open(self.path, "r") as fp:
            for line in fp.readlines():
                if not line.strip():
                    continue
                if line.sartswith('#'):
                    continue
                k, v = line.split("=", 1)
                self.settings[k.strip().lower()] = v.str()

    def save(self):
        with open(self.path, "w") as fp:
            for key in sorted(self.settings.keys()):
                fp.write("%s = %s\n" % (key, self.settings[key]))

    def __getitem__(self, key):
        return self.settings[key]

    def __setitem__(self, key, value):
        self.settings[key] = value
        self.save()


class VMWareDriver(NodeDriver):

    """ This is an implementation of a libcloud driver for VMWare, that is
    used in preference to libvirt because it is better. """

    type = Provider.VMWARE
    name = "vmware"
    website = "http://www.vmware.com/products/fusion/"
    connectionCls = Connection

    def __init__(self, yaybu_root="~/.yaybu", vmrun=None, hosttype=None):
        super(VMWareDriver, self).__init__(None)
        self.vmrun = vmrun or self._find_vmrun()
        self.hosttype = hosttype or self._find_hosttype()
        self.image_cache = VMBoxCollection(root=yaybu_root)

    def _find_vmrun(self):
        known_locations = [
            "/Applications/VMWare Fusion.app/Contents/Library",
            "/usr/bin",
            ]
        for dir in known_locations:
            path = os.path.join(dir, "vmrun")
            if os.path.exists(path):
                return path
        raise LibcloudError('VMWareDriver requires \'vmrun\' executable to be present on system')

    def _find_hosttype(self):
        default_hosttypes = [
            'ws',
            'fusion',
            'player',
            ]
        for hosttype in default_hosttypes:
            command = [self.vmrun, "-T", hosttype, "list"]
            try:
                resp = self.connection.request(command)
            except LibcloudError:
                continue
            else:
                return hosttype
        raise LibcloudError('VMWareDriver is unable to find a default host type. Please specify the hosttype argument')

    def _action(self, *params, **kwargs):
        capture_output = kwargs.get('capture_output', True)
        command = [self.vmrun, "-T", self.hosttype] + list(params)
        logger.debug("Executing %r" % (" ".join(command),))
        return self.connection.request(command, capture_output=capture_output).body

    def list_images(self, location=None):
        ## TODO
        ## list the template images from the cache
        ## provide friendly names somehow, perhaps deduping on leafname or something
        if not location:
            location = self.vm_library
        locs = []
        for match in glob.glob(os.path.join(location, "*", "*.vmx")):
            locs.append(NodeImage(id=match, name="VMWare Image", driver=self))
        return locs

    def list_sizes(self, location=None):
        return [
            NodeSize("small", "small", 1024, 0, 0, 0, self),
            NodeSize("medium", "medium", 4096, 0, 0, 0, self),
            NodeSize("large", "large", 8192, 0, 0, 0, self),
            ]

    def list_locations(self):
        return []

    def list_nodes(self):
        nodes = []
        lines = iter(self._action("list").strip().splitlines())
        lines.next() # Skip the summary line
        for line in lines:
            if not line.strip():
                continue
            n = Node(line.strip(), line.strip(), NodeState.UNKNOWN, None, None, self)
            n.name = self._action("readVariable", n.id, "runtimeConfig", "displayName").strip()
            ip = self._action("readVariable", n.id, "guestVar", "ip").strip()
            if ip:
                n.public_ips = [ip]
                n.state = NodeState.RUNNING
            nodes.append(n)
        return nodes

    def _image_smells_remote(self, imageid):
        remote_smells = ('http://', 'https://', 'file://')
        for smell in remote_smells:
            if imageid.startswith(smell):
                return True
        return False

    def create_node(self, name, size, image, **kwargs):
        """ Create a new VM from a template VM and start it.
        """
        ## TODO: look at image.id, which is the name of the template image
        ## i.e. it is either an http or file URL then use the image cache to
        ## fetch it if necessary, then use the new location below to actually
        ## create the new vm
        ## self.yaybu_context is the context object that I need to do the progress
        ## bar with
        ##
        ## with self.yaybu_context.ui.progressbar as p:
        ##     p.progress(50)
        ##
        ## then install credentials as per the existing code
        ## provide options for create_node for which sort of credential installation
        ## to use -
        ##
        ## https://github.com/apache/libcloud/blob/trunk/libcloud/compute/base.py#L518
        ##
        ## support all 2 options, ssh_key and password
        ##
        ## for extra marks, detect the terminal width

        if self._image_smells_remote(image.id):
            source = self.image_cache.install(image.id, context=self.yaybu_context)
        else:
            source = os.path.expanduser(image.id)
        if not os.path.exists(source):
            raise LibcloudError("Base image %s not found" % source)

        target_dir = os.path.join(self.image_cache.instancedir, str(uuid.uuid4()))
        target = os.path.join(target_dir, "vm.vmx")

        target_parent = os.path.dirname(target_dir)
        if not os.path.exists(target_parent):
            os.makedirs(target_parent)

        logger.debug("Creating node %r" % (name,))
        # First try to clone the VM with the VMWare commands. We do this in
        # the hope that they know what the fastest and most efficient way to
        # clone an image is. But if that fails we can just copy the entire
        # image directory.
        try:
            self._action("clone", source, target)
        except LibcloudError:
            src_path = os.path.dirname(source)
            shutil.copytree(src_path, target_dir)
            os.rename(os.path.join(target_dir, os.path.basename(source)), target)

        node = Node(target, name, NodeState.PENDING, None, None, self)

        # If a NodeSize is provided then we can control the amount of RAM the
        # VM has. Number of CPU's would be easy to scale too, but this isn't
        # exposed on a NodeSize

        # if size:
        #     if size.ram:
        #        self.ex_set_runtime_variable(node, "displayName", name, str(size.ram))
        #        self._action("writeVariable", target, "runtimeConfig", "memsize", str(size.ram))

        self._action("start", target, "nogui", capture_output=False)
        self.ex_set_runtime_variable(node, "displayName", name)
        return Node(target, name, NodeState.PENDING, None, None, self)

    def reboot_node(self, node):
        logger.debug("Rebooting node %r" % (node.id,))
        self._action("reset", node.id, "hard")
        node.state = NodeState.REBOOTING

    def destroy_node(self, node):
        logger.debug("Destroying node %r" % (node.id,))
        self._action("stop", node.id, "hard")
        self._action("deleteVM", node.id)
        shutil.rmtree(os.path.dirname(node.id))

    def ex_get_runtime_variable(self, node, variable):
        value = self._action("readVariable", node.id, "runtimeConfig", variable)
        logger.debug("Read variable %r from node %r, value was %r" % (variable, node.id, value))
        return value

    def ex_set_runtime_variable(self, node, variable, value):
        logger.debug("Setting runtime variable %r on node %r to %r" % (variable, node.id, value))
        self._action("writeVariable", node.id, "runtimeConfig", variable, value)

class VMException(Exception):
    pass

class VMBoxImage:

    """ A compressed and packaged virtual machine image """

    def __init__(self, path):
        self.path = path

    def extract(self, destdir):
        """ Extract the compressed image into the destination directory, with
        the specified name. """
        if os.path.exists(destdir):
            raise VMException("%r exists, and will not be clobbered" % (destdir,))
        os.mkdir(destdir)
        with zipfile.ZipFile(self.path, "r", zipfile.ZIP_DEFLATED, True) as z:
            for f in z.namelist():
                pathname = os.path.join(destdir, f)
                print "Writing", pathname
                zf = z.open(f, "r")
                of = open(pathname, "w")
                while True:
                    data = zf.read(8192)
                    if not data:
                        break
                    of.write(data)

    def compress(self, srcdir):
        """ Create the package from the specified source directory. """
        if not os.path.isdir(srcdir):
            raise VMException("%r does not exist, is not accessible or is not a directory" % (srcdir,))
        with zipfile.ZipFile(self.path, "w", zipfile.ZIP_DEFLATED, True) as z:
            z.comment = "Created by Yaybu"
            for f in sorted(os.listdir(srcdir)):
                if f.endswith("nvram") or ".vm" in f:
                    print "Packing", f
                    z.write(os.path.join(srcdir, f), f)
            print "Done."



class VMBoxCollection:

    """ A collection of archive files, some of which may be remote and some
    local, with a local cache and a set of them that are expanded and ready
    for use. """

    ## TODO: What about file and directory modes? Rely on umask?

    ImageClass = VMBoxImage

    def __init__(self, root="~/.yaybu"):
        self.root = os.path.expanduser(root)

        # a set of images that are only cloned, with additional information
        # needed to start and connect to them correctly
        self.librarydir = os.path.join(self.root, "vmware", "library")

        # a cache of downloaded image files
        self.cachedir = os.path.join(self.root, "vmware", "cache")

        # instances that may be started and running
        self.instancedir = os.path.join(self.root, "vmware", "instances")

        self.setupdirs()
        self.cache = VMBoxCache(self.cachedir)

    def setupdirs(self):
        """ Create directories if required """
        for d in self.librarydir, self.cachedir, self.instancedir:
            if not os.path.exists(d):
                os.makedirs(d)

    def guess_name(self, uri):
        """ Use the name of the file with the extension stripped off """
        path = urlparse.urlparse(uri).path
        leaf = path.split("/")[-1]
        if not leaf:
            raise VMException("Cannot guess name for %r" % (uri,))
        return leaf.rsplit(".", 1)[0]

    def _locate_vmx(self, path):
        for f in os.listdir(path):
            if f.endswith(".vmx"):
                return os.path.join(path, f)

    def install(self, uri, name=None, context=None):
        """ Fetches the specified uri into the cache and then extracts it
        into the library.  If name is None then a name is made up. """
        if name is None:
            name = self.guess_name(uri)
        destdir = os.path.join(self.librarydir, name)
        if not os.path.exists(destdir):
            self.cache.insert(uri, context)
            vmi = self.ImageClass(self.cache.image(uri))
            vmi.extract(destdir)
        return self._locate_vmx(destdir)

class RemoteVMBox:

    """ Provides tooling around remote images, specifically hash verification
    and image signing. """

    def __init__(self, location):
        self.location = location

    def get_hash(self):
        """ Try methods in order until one returns something other than None.
        This is the MD5. """
        methods = (self._hash_headers,
                   self._hash_detached)
        for m in methods:
            md5 = m()
            if md5 is not None:
                return md5

    def _hash_headers(self):
        """ Fetch the MD5 hash from the first "Content-MD5" header if
        present. """
        rq = urllib2.Request(self.location)
        rq.get_method = lambda: 'HEAD'
        rs = urllib2.urlopen(rq)
        headers = rs.info().getheaders("Content-MD5")
        if headers:
            md5 = headers[0]
        else:
            md5 = None
        return md5

    def _hash_detached(self):
        """ Fetch the hash from a detached text file alongside the original
        """
        md5_location = self.location + ".md5"
        try:
            md5 = urllib2.urlopen(md5_location).read()
        except urllib2.URLError:
            md5 = None
        return md5

    def download(self, dst, progress, batch_size=8192):
        """ Download the file and calculate its hash """
        self.hash = self.get_hash()
        h = hashlib.md5()
        downloaded = 0
        percent = 0
        fout = open(dst, "w")
        fin = urllib2.urlopen(self.location)
        content_length = int(fin.headers['content-length'])
        while True:
            data = fin.read(batch_size)
            if not data: break
            h.update(data)
            fout.write(data)
            downloaded += len(data)
            percent = int(float(downloaded) / content_length * 100)
            progress(percent)
        fin.close()
        fout.close()
        if self.hash != None:
            if h.hexdigest() != self.hash:
                raise ValueError("Wrong hash. Calculated %r != Correct %r" % (h.hexdigest(), self.hash))

class VMBoxCache:

    """ A cache of compressed instances. Each item in the cache is identified
    by the name that was used to retrieve it - we don't have a concept of an
    embedded name or a global name register. """

    # The cache has one directory per box, with a metadata json file describing
    # what we call the file and when it was retrieved
    # there may be additional directories and files in the cache that are ignored
    # only directories containing a metadata are considered

    def __init__(self, cachedir):
        self.cachedir = cachedir
        self.items = {}
        self.scan()

    def scan(self):
        for item in os.listdir(self.cachedir):
            ip = os.path.join(self.cachedir, item)
            if os.path.isdir(ip):
                mp = os.path.join(ip, "metadata")
                if os.path.exists(mp):
                    md = json.load(open(mp))
                    self.items[md['name']] = item

    def insert(self, location, context):
        """ Insert an item into the cache from a specified location.

        Args:
            location: A url to the compressed box
            context: A context object used for progress reporting

        """
        if self.items.has_key(location):
            return
        r = RemoteVMBox(location)
        name = str(uuid.uuid4())
        path = os.path.join(self.cachedir, name)
        os.mkdir(path)
        mp = os.path.join(path, "metadata")
        ip = os.path.join(path, "image")
        with context.ui.progress(100) as p:
            r.download(ip, p.progress)
        metadata = {
            'name': location,
            'created': str(datetime.datetime.now()),
            'hash': r.hash
        }
        json.dump(metadata, open(mp, "w"))
        return name

    def image(self, location):
        if not self.items.has_key(location):
            raise KeyError("Item is not in cache")
        return os.path.join(self.cachedir, self.items[location], "image")

