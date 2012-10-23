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

import os
import logging
import pickle
import subprocess
import StringIO

import yay
from yay.openers import Openers
from yay.errors import LanguageError, NotFound, NotModified, get_exception_context

from yaybu.core import change, resource, vfs
from yaybu.core.error import ParseError, MissingAsset, Incompatible, UnmodifiedAsset
from yaybu.core.protocol.client import HTTPConnection
from yaybu.core.shell import Shell

logger = logging.getLogger("runcontext")

class RunContext(object):
    
    """ A context object that holds the environment required to run yaybu. """

    simulate = False
    ypath = ()
    verbose = 0

    def __init__(self, configfile, resume=False, no_resume=False, user="root", 
                 host=None, ypath=(), simulate=False, verbose=2,
                 env_passthrough=()):
        self.path = []
        self.ypath = []
        self.options = {}
        self._config = None
        self._bundle = None

        self.resume = resume
        self.no_resume = no_resume
        self.user = user

        self.set_host(host)
        self.connect_user = None
        self.port = None

        if os.path.exists("/etc/yaybu"):
            self.options = yay.load_uri("/etc/yaybu")

        logger.debug("Invoked with ypath: %r" % (ypath, ))
        logger.debug("Environment YAYBUPATH: %r" % os.environ.get("YAYBUPATH", ""))
        self.simulate = simulate
        self.ypath = list(ypath)
        self.verbose = verbose

        if "PATH" in os.environ:
            for term in os.environ["PATH"].split(":"):
                self.path.append(term)

        if "YAYBUPATH" in os.environ:
            for term in os.environ["YAYBUPATH"].split(":"):
                self.ypath.append(term)

        if not len(self.ypath):
            self.ypath.append(os.getcwd())

        self.configfile = configfile

        self.setup_shell(env_passthrough)
        self.setup_changelog()

        self.vfs = vfs.Local(self)
        
    def set_host(self, host):
        self.host = host
        if self.host:
            if "@" in self.host:
                self.connect_user, self.host = self.host.split("@", 1)
            if ":" in self.host:
                self.host, self.port = self.host.split(":", 1)
        extra = {
            "yaybu": {
                "host": self.host,
                }
            }
        if self._config:
            self._config.add(extra)

    def setup_shell(self, environment):
        self.shell = Shell(context=self,
            verbose=self.verbose,
            simulate=self.simulate,
            environment=environment)

    def setup_changelog(self):
        self.changelog = change.ChangeLog(self)
        self.changelog.configure_session_logging()

    def locate(self, paths, filename):
        if filename.startswith("/"):
            return filename
        for prefix in paths:
            candidate = os.path.realpath(os.path.join(prefix, filename))
            logger.debug("Testing for existence of %r" % (candidate,))
            if os.path.exists(candidate):
                return candidate
            logger.debug("%r does not exist" % candidate)
        raise MissingAsset("Cannot locate file %r" % filename)

    def locate_file(self, filename):
        """ Locates a file by referring to the defined yaybu path. If the
        filename starts with a / then it is absolutely rooted in the
        filesystem and will be returned unmolested. """
        return self.locate(self.ypath, filename)

    def locate_bin(self, filename):
        """ Locates a binary by referring to the defined yaybu path and PATH. If the
        filename starts with a / then it is absolutely rooted in the
        filesystem and will be returned unmolested. """
        return self.locate(self.ypath + self.path, filename)

    def set_config(self, config):
        """ Rather than have yaybu load a config you can provide one """
        self._config = config

    def get_config(self):
        if self._config:
            return self._config

        try:
            yay_config = {
                "openers": {
                    "packages": {
                        "cachedir": os.path.expanduser("~/.yaybu/packages"),
                        },
                    },
                }
            c = yay.config.Config(searchpath=self.ypath, config=yay_config)

            if self.host:
                extra = {
                    "yaybu": {
                        "host": self.host,
                        }
                    }
                c.add(extra)

            defaults = os.path.expanduser("~/.yaybu/defaults.yay")
            if os.path.exists(defaults):
                c.load_uri(defaults)

            defaults_gpg = os.path.expanduser("~/.yaybu/defaults.yay.gpg")
            if os.path.exists(defaults_gpg):
                c.load_uri(defaults_gpg)

            c.load_uri(self.configfile)

            self._config = c
            return c

        except yay.errors.Error, e:
            msg = e.get_string()
            if self.verbose > 2:
                msg += "\n" + get_exception_context()
            raise ParseError(e.get_string())

    def set_bundle(self, bundle):
        self._bundle = bundle

    def get_bundle(self):
        if self._bundle:
            return self._bundle

        cfg = self.get_config().lookup("resources")
        bundle = resource.ResourceBundle.create_from_yay_expression(cfg, verbose_errors=self.verbose>2)
        bundle.bind()
        self._bundle = bundle

        return bundle

    def get_decrypted_file(self, filename, etag=None):
        p = subprocess.Popen(["gpg", "-d", self.locate_file(filename)], stdout=subprocess.PIPE)
        return p.stdout

    def get_file(self, filename, etag=None):
        try:
            return Openers(searchpath=self.ypath).open(filename, etag)
        except NotModified, e:
            raise UnmodifiedAsset(str(e))
        except NotFound, e:
            raise MissingAsset(str(e))

    def get_data_path(self, path=None):
        if not path:
            return "/var/run/yaybu"
        return os.path.join("/var/run/yaybu", path)

class RemoteRunContext(RunContext):

    def __init__(self, configfile, **kwargs):
        self.connection = HTTPConnection()
        self.check_versions()
        super(RemoteRunContext, self).__init__(configfile, **kwargs)
        
    def check_versions(self):
        self.connection.request("GET", "/about")
        rsp = self.connection.getresponse()

        if rsp.status != 200:
            self.features = []
            self.versions = {"Yaybu": "0", "yay": "0"}
        else:
            self.features = rsp.getheader("features", "").split(",")
            self.versions = {
                "Yaybu": rsp.getheader("Yaybu", "0"),
                "yay": rsp.getheader("yay", "0"),
                }
        logger.debug("target versions: yaybu %r yay %r" % (self.versions['Yaybu'], self.versions['yay']))

        import pkg_resources
        if pkg_resources.parse_version(self.versions["Yaybu"]) <= pkg_resources.parse_version("0"):
            raise Incompatible("You require a newer version of 'Yaybu' to deploy to this server")

        if pkg_resources.parse_version(self.versions["yay"]) <= pkg_resources.parse_version("0"):
            raise Incompatible("You require a newer version of 'yay' to deploy to this server")

    def setup_changelog(self):
        self.changelog = change.RemoteChangeLog(self)
        self.changelog.configure_session_logging()

    def get_config(self):
        self.connection.request("GET", "/config")
        rsp = self.connection.getresponse()
        c = yay.config.Config()
        c.add(pickle.loads(rsp.read()))
        return c

    def get_decrypted_file(self, filename, etag=None):
        self.connection.request("GET", "/encrypted/" + filename)
        rsp = self.connection.getresponse()
        return rsp

    def get_file(self, filename, etag=None):
        if filename.startswith("/"):
            return super(RemoteRunContext, self).get_file(filename, etag)

        headers = {}
        if etag:
            headers["If-None-Match"] = etag

        self.connection.request("GET", "/files/?path=" + filename, '', headers)

        rsp = self.connection.getresponse()

        if rsp.status == 304:
            raise UnmodifiedAsset("Cannot fetch %r as it should be cached locally" % filename)

        if rsp.status == 404:
            raise MissingAsset("Cannot fetch %r" % filename)

        rsp.etag = rsp.msg.get("etag", None)

        return rsp

