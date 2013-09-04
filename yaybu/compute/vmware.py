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
# libcloud/common/process.py

import os
import shlex
import subprocess
from pipes import quote
import binascii

from libcloud.common.types import *
from libcloud.compute.base import NodeAuthPassword, NodeAuthSSHKey
import logging
import json
import urllib2
import uuid
import datetime
import urlparse
import tempfile
from functools import partial
import time

import zipfile
from yaybu.util import ZipFile

logger = logging.getLogger("yaybu.parts.compute.vmware")

class VMRunError(LibcloudError):
    pass

class FileAlreadyExistsError(VMRunError):

    def __init__(self):
        self.value = "File or directory already exists"

class Response(object):

    def __init__(self, status, body, error):
        self.status = status
        self.body = body
        self.error = error

        if not self.success():
            raise self.parse_error()

        self.object = self.parse_body()

    def parse_body(self):
        return self.body

    def parse_error(self):
        if self.body == 'Error: The file already exists\n':
            raise FileAlreadyExistsError()
        raise ProviderError(self.body + " " + self.error, self.error)

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

class VMWareVM:

    def __init__(self, instancedir, id=None):
        self.instancedir = instancedir
        self.id = id or self._gen_id()

    def _gen_id(self):
        return str(uuid.uuid4())

    @property
    def directory(self):
        return os.path.join(self.instancedir, self.id)

    @property
    def vmx(self):
        return os.path.join(self.directory, "vm.vmx")

    @property
    def parent(self):
        return os.path.dirname(self.directory)

    def setup(self):
        """ Create the parent directories if required """
        if not os.path.isdir(self.parent):
            os.mkdir(self.parent)

    def info(self, name):
        infofile = os.path.join(self.directory, "VM-INFO")
        d = json.load(open(infofile))
        return d[name]

    def set_info(self, name, value):
        infofile = os.path.join(self.directory, "VM-INFO")
        d = json.load(open(infofile))
        d[name] = value
        json.dump(open(infofile, "w"))

    @property
    def username(self):
        return self.info("username")

    @property
    def password(self):
        return self.info("password")

    def _get_name(self):
        return self.info("name")

    def _set_name(self, name):
        self.set_info("name", name)

    name = property(_get_name, _set_name)



class VMWareDriver(NodeDriver):

    """ This is an implementation of a libcloud driver for VMWare, that is
    used in preference to libvirt because it is better. """

    type = Provider.VMWARE
    name = "vmware"
    website = "http://www.vmware.com/products/fusion/"
    connectionCls = Connection
    features = {'create_node': ['ssh_key', 'password']}

    def __init__(self, yaybu_root="~/.yaybu", vmrun=None, hosttype=None):
        super(VMWareDriver, self).__init__(None)
        self.vmrun = vmrun or self._find_vmrun()
        self.hosttype = hosttype or self._find_hosttype()
        self.machines = VMBoxLibrary(root=yaybu_root)

    def ex_start(self, node):
        """
        Start a stopped node.

        @param node: Node which should be used
        @type  node: L{Node}

        @rtype: C{bool}
        """
        with self.yaybu_context.ui.throbber("Starting VM") as t:
            self._action("start", node.id, "nogui", capture_output=False)
            node.state = NodeState.RUNNING
        with self.yaybu_context.ui.throbber("Waiting for VM to boot completely") as t:
            while not self._decorate_node(node):
                time.sleep(1)
                t.throb()


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

    def _guest_action(self, target, command, *params):
        self._action("-gu", target.username, "-gp", target.password,
                     command, target.vmx, *params,
                     capture_output=True)

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

    def _list_running(self):
        """ List running virtual machines """
        lines = iter(self._action("list").strip().splitlines())
        lines.next() # Skip the summary line
        for line in lines:
            if not line.strip():
                continue
            yield line.strip()

    def _decorate_node(self, node):
        """ Add ips. Returns True if it successfully decorated it, False if
        it failed and None if the node was not running. """
        if node.state == NodeState.RUNNING:
            ip = self._action("readVariable", node.id, "guestVar", "ip").strip()
            if ip:
                node.public_ips = [ip]
                return True
            return False
        return None

    def list_nodes(self):
        """ List all of the nodes the driver knows about. """
        nodes = []
        running = list(self._list_running())
        for vm in self.machines.instances():
            state = NodeState.RUNNING if vm.vmx in running else NodeState.UNKNOWN
            n = Node(vm.vmx, vm.vmx, state, None, None, self)
            self._decorate_node(n)
            nodes.append(n)
        return nodes

    def _image_smells_remote(self, imageid):
        remote_smells = ('http://', 'https://', 'file://')
        for smell in remote_smells:
            if imageid.startswith(smell):
                return True
        return False

    def apply_auth_password(self, vmrun, username, password):
        """ Set the password of the specified username to the provided password """
        with self.yaybu_context.ui.throbber("Applying new password credentials") as t:
            t.throb()
            vmrun("runProgramInGuest", "/usr/bin/sudo", "/bin/bash", "-c", "echo '%s:%s'|/usr/sbin/chpasswd" % (username, password))

    def apply_auth_ssh(self, vmrun, username, pubkey):
        """ Add the provided ssh public key to the specified user's authorised keys """
        ## TODO actually find homedir properly
        ## TODO find sudo properly
        with self.yaybu_context.ui.throbber("Applying new SSH credentials") as t:
            homedir = "/home/%s" % username
            tmpfile = tempfile.NamedTemporaryFile(delete=False)
            tmpfile.write(pubkey)
            tmpfile.close()
            t.throb()
            try:
                vmrun("createDirectoryInGuest", "%s/.ssh" % homedir)
            except FileAlreadyExistsError:
                pass
            t.throb()
            vmrun("copyFileFromHostToGuest", tmpfile.name, "%s/.ssh/authorized_keys" % homedir)
            t.throb()
            vmrun("runProgramInGuest", "/bin/chmod", "0700", "%s/.ssh" % homedir)
            t.throb()
            vmrun("runProgramInGuest", "/bin/chmod", "0600", "%s/.ssh/authorized_keys" % homedir)
            t.throb()
            os.unlink(tmpfile.name)

    def apply_auth(self, target, auth):
        """ Apply the specified authentication credentials to the virtual machine. """
        vmrun = partial(self._guest_action, target)
        if isinstance(auth, NodeAuthPassword):
            self.apply_auth_password(vmrun, auth.username, auth.password)
        if isinstance(auth, NodeAuthSSHKey):
            self.apply_auth_ssh(vmrun, auth.username, auth.pubkey)

    def _get_and_check_auth(self, auth):
        """
        Helper function for providers supporting L{NodeAuthPassword} or
        L{NodeAuthSSHKey}

        Validates that only a supported object type is passed to the auth
        parameter and raises an exception if it is not.

        If no L{NodeAuthPassword} object is provided but one is expected then a
        password is automatically generated.
        """

        if isinstance(auth, NodeAuthPassword):
            if 'password' in self.features['create_node']:
                return auth
            raise LibcloudError(
                'Password provided as authentication information, but password'
                'not supported', driver=self)

        if isinstance(auth, NodeAuthSSHKey):
            if 'ssh_key' in self.features['create_node']:
                return auth
            raise LibcloudError(
                'SSH Key provided as authentication information, but SSH Key'
                'not supported', driver=self)

        if 'password' in self.features['create_node']:
            value = os.urandom(16)
            value = binascii.hexlify(value).decode('ascii')
            return NodeAuthPassword(value, generated=True)

        if auth:
            raise LibcloudError(
                '"auth" argument provided, but it was not a NodeAuthPassword'
                'or NodeAuthSSHKey object', driver=self)

    def _get_source(self, image):
        """ If the source looks like it is remote then fetch the image and
        extract it into the library directory, otherwise use it directly. """
        if self._image_smells_remote(image.id):
            source = self.machines.get(image.id, context=self.yaybu_context)
        else:
            source = os.path.expanduser(image.id)
        if not os.path.exists(source):
            raise LibcloudError("Base image %s not found" % source)
        return source

    def _get_target(self):
        """ Create a new target in the instance directory """
        target = VMWareVM(self.machines.instancedir)
        target.setup()
        return target

    def _clone(self, source, target):
        """ Try to clone the VM with the VMWare commands. We do this in the
        hope that they know what the fastest and most efficient way to clone
        an image is. But if that fails we can just copy the entire image
        directory. """
        with self.yaybu_context.ui.throbber("Cloning template VM") as t:
            try:
                self._action("clone", source, target.vmx)
            except LibcloudError:
                src_path = os.path.dirname(source)
                shutil.copytree(src_path, target.directory)
                os.rename(os.path.join(target.directory, os.path.basename(source)), target.vmx)

    def create_node(self, name, size, image, auth=None, **kwargs):
        """ Create a new VM from a template VM and start it.
        """

        auth = self._get_and_check_auth(auth)
        source = self._get_source(image)
        target = self._get_target()
        self._clone(source, target)
        target.name = name
        node = Node(target.vmx, name, NodeState.PENDING, None, None, self)

        # If a NodeSize is provided then we can control the amount of RAM the
        # VM has. Number of CPU's would be easy to scale too, but this isn't
        # exposed on a NodeSize

        # if size:
        #     if size.ram:
        #        self.ex_set_runtime_variable(node, "displayName", name, str(size.ram))
        #        self._action("writeVariable", target, "runtimeConfig", "memsize", str(size.ram))

        self.ex_start(node)
        self.ex_set_runtime_variable(node, "displayName", name)
        self.apply_auth(target, auth)
        return node

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

    def _zcopy(self, pathname, zfile, name):
        """ Copy the contents of a file out of a zipfile. """
        zf = zfile.open(name, "r")
        of = open(pathname, "w")
        while True:
            data = zf.read(8192)
            if not data:
                break
            of.write(data)

    def _store_metadata(self, destdir, metadata):
        json.dump(metadata, open(os.path.join(destdir, "VM-INFO"), "w"))

    def extract(self, destdir, context, metadata):
        """ Extract the compressed image into the destination directory, with
        the specified name. """
        with context.ui.throbber("Extracting virtual machine") as t:
            with ZipFile(self.path, "r", zipfile.ZIP_DEFLATED, True) as z:
                for f in z.namelist():
                    if f == "VM-INFO":
                        metadata.update(json.loads(z.open(f, "r").read()))
                    else:
                        pathname = os.path.join(destdir, f)
                        self._zcopy(pathname, z, f)
                    t.throb()
            self._store_metadata(destdir, metadata)

    def compress(self, srcdir, username, password):
        """ Create the package from the specified source directory. """
        if not os.path.isdir(srcdir):
            raise VMException("%r does not exist, is not accessible or is not a directory" % (srcdir,))
        with ZipFile(self.path, "w", zipfile.ZIP_DEFLATED, True) as z:
            z.comment = "Created by Yaybu"
            for f in sorted(os.listdir(srcdir)):
                if f.endswith("nvram") or ".vm" in f:
                    print "Packing", f
                    z.write(os.path.join(srcdir, f), f)
            z.writestr("VM-INFO", json.dumps({'username': username, 'password': password}))
            print "Done."

class RemoteVMBox:

    """ Provides tooling around remote images, specifically hash verification
    and image signing. """

    def __init__(self, location, tempdir, context):
        self.location = location
        self._tempdir = tempdir
        self.context = context

    def __enter__(self):
        """ Fetch an item into the temporary directory from a remote location

        Args:
            location: A url to the compressed box
            context: A context object used for progress reporting

        Returns: the full path to the downloaded package directory

        """
        self.dir = tempfile.mkdtemp(dir=self._tempdir)
        self.image = os.path.join(self.dir, "image")
        with self.context.ui.throbber("Downloading packed VM") as t:
            pass
        with self.context.ui.progress(100) as p:
            self.download(self.image, p.progress)
        self.metadata = {
            'url': self.location,
            'created': str(datetime.datetime.now()),
            'hash': self.hash
        }
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        shutil.rmtree(self.dir)

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
        if self.hash is None:
            self.hash = h.hexdigest()
        else:
            if h.hexdigest() != self.hash:
                raise ValueError("Wrong hash. Calculated %r != Correct %r" % (h.hexdigest(), self.hash))

class VMBoxLibrary:

    """ A library of virtual machines, and a mechanism for adding packaged
    virtual machines to the library from local or remote locations.

    Some of these VMs are "templates" and not intended to be run from their
    existing location. Some are copies of the templates and are in use.

    The directory structure resembles:

    ~/.yaybu/vmware/
        /instances/
            /<UUID>/
                VM-INFO
                <vmware files>
        /library/
            /<UUID>/
                metadata
                image/
                    <vmware files>
        /temp/
            <UUID>/
                <files created during download and extraction>

    """

    # This is the class that represents the images
    ImageClass = VMBoxImage

    def __init__(self, root="~/.yaybu"):
        self.root = os.path.expanduser(root)
        self.library = {}
        # a set of images that are only cloned
        self.librarydir = os.path.join(self.root, "vmware", "library")
        # instances that may be started and running
        self.instancedir = os.path.join(self.root, "vmware", "instances")
        # A temporary directory, we put it here so we know we have enough room
        self.tempdir = os.path.join(self.root, "vmware", "temp")
        self.setupdirs()
        self.scan()

    def setupdirs(self):
        """ Create directories if required """
        for d in self.librarydir, self.instancedir, self.tempdir:
            if not os.path.exists(d):
                os.makedirs(d)

    def scan(self):
        """ Scan the library and populate self.library """
        for item in os.listdir(self.librarydir):
            ip = os.path.join(self.librarydir, item)
            if os.path.isdir(ip):
                mp = os.path.join(ip, "VM-INFO")
                if os.path.exists(mp):
                    md = json.load(open(mp))
                    self.library[md['url']] = item

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

    def fetch(self, uri, name, context):
        """ Fetch the URI """
        if name is None:
            name = self.guess_name(uri)
        destdir = os.path.join(self.librarydir, name)
        if os.path.exists(destdir):
            vminfo = os.path.join(destdir, 'VM-INFO')
            origuri = json.load(open(vminfo))['url']
            raise VMException("Requested to download %s from %s but already downloaded from %s" % (name, uri, origuri))
        with RemoteVMBox(uri, self.tempdir, context) as box:
            tmp = tempfile.mkdtemp(dir=self.tempdir)
            vmi = self.ImageClass(box.image)
            vmi.extract(tmp, context, box.metadata)
            os.rename(tmp, destdir)
            self.library[uri] = name

    def get(self, uri, context=None, name=None):
        """ Fetches the specified uri into the cache and then extracts it
        into the library.  If name is None then a name is made up.

        Arguments:
            name: the suggested name for the downloaded VM. Note that
                  if the VM is already present it may have a different name, but will
                  be used anyway.


        """
        if not uri in self.library:
            self.fetch(uri, name, context)
        name = self.library[uri]
        return self._locate_vmx(os.path.join(self.librarydir, name))

    def instances(self):
        """ Return a generator of VMWareVM objects. """
        for i in os.listdir(self.instancedir):
            yield VMWareVM(self.instancedir, i)
