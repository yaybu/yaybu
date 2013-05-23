# Copyright 2012 Isotoma Limited
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

from yay.openers.base import Openers, SearchpathFromGraph
from yay.errors import Error, NoMatching, get_exception_context
from yay.config import Config as BaseConfig
from yay import ast

from yaybu.core.error import ParseError, ArgParseError
from yaybu.core.util import memoized
from yaybu.core.state import StateStorageType, SimulatedStateStorageAdaptor
from yaybu import changes


class YaybuArg:

    def __init__(self, name, type_='string', default=None, help=None):
        self.name = name.lower()
        self.type = type_.lower()
        self.default = default
        self.help = help
        self.value = None

    def set(self, value):
        self.value = value

    def _get(self):
        if self.value is None and self.default is not None:
            return self.default
        else:
            return self.value

    def get(self):
        return self.convert(self._get())

    def convert(self, value):
        if self.type == 'string':
            return value
        elif self.type == 'integer':
            try:
                return int(value)
            except ValueError:
                raise ArgParseError("Cannot convert %r to an int for argument %r" % (value, self.name))
        elif self.type == 'boolean':
            if type(value) == type(True):
                # might already be boolean
                return value
            if value.lower() in ('no', '0', 'off', 'false'):
                return False
            elif value.lower() in ('yes', '1', 'on', 'true'):
                return True
            raise ArgParseError("Cannot parse boolean from %r for argument %r" % (value, self.name))
        else:
            raise ArgParseError("Don't understand %r as a type for argument %r" % (self.type, self.name))


class YaybuArgParser:

    def __init__(self, *args):
        self.args = {}
        for a in args:
            self.add(a)

    def add(self, arg):
        if arg.name in self.args:
            raise ArgParseError("Duplicate argument %r specified" % (arg.name,))
        self.args[arg.name] = arg

    def parse(self, **arguments):
        for name, value in arguments.items():
            if name not in self.args:
                raise ArgParseError("Unexpected argument %r provided" % (name,))
            self.args[name].set(value)
        return dict(self.values())

    def values(self):
        for a in self.args.values():
            yield (a.name, a.get())


class Config(BaseConfig):

    """
    This class adapts ``yay.config.Config`` for use in Yaybu. In particular it
    helps to ensure that Yaybu API users only have to deal with Yaybu
    exceptions and not yay exceptions. It also applies so default Yaybu
    policies like looking in ``~/.yaybu/`` for certain things.
    """

    def __init__(self, context=None, hostname=None, searchpath=None):
        self.context = context

        config = {
            "openers": {
                "packages": {
                    "cachedir": os.path.expanduser("~/.yaybu/packages"),
                    },
                },
            }

        super(Config, self).__init__(searchpath=searchpath, config=config)

        from yaybu import parts
        self.builtins = {
            "Compute": ast.PythonClassFactory(parts.Compute),
            "Provisioner": ast.PythonClassFactory(parts.Provision),
            "LoadBalancer": ast.PythonClassFactory(parts.LoadBalancer),
            "Zone": ast.PythonClassFactory(parts.Zone),
            "Heroku": ast.PythonClassFactory(parts.Heroku),
            }

        if hostname:
            self.set_hostname(hostname)

        defaults = os.path.expanduser("~/.yaybu/defaults.yay")
        if os.path.exists(defaults):
            self.load_uri(defaults)

        defaults_gpg = os.path.expanduser("~/.yaybu/defaults.yay.gpg")
        if os.path.exists(defaults_gpg):
            self.load_uri(defaults_gpg)

        self.changelog = changes.ChangeLog(self)
        self.changelog.configure_session_logging()

    def setup_openers(self, searchpath):
        self.add({"yaybu": {"searchpath": searchpath or []}})
        self.openers = Openers(searchpath=SearchpathFromGraph(self.yaybu.searchpath))

    def set_arguments(self, **arguments):
        parser = YaybuArgParser()

        try:
            args = list(self.yaybu.options)
        except NoMatching:
            args = []

        for arg in args:
            yarg = YaybuArg(
                str(arg.name),
                arg.type.as_string('string'),
                arg.default.as_string(None),
                arg.help.as_string(None),
                )
            parser.add(yarg)

        self.add({
            "yaybu": {
                "argv": parser.parse(**arguments),
                }
            })

    def set_arguments_from_argv(self, argv):
        arguments = {}
        for arg in argv:
            name, value = arg.split("=", 1)
            if name in arguments:
                raise ArgParseError("Duplicate argument %r specified" % (name,))
            arguments[name] = value
        self.set_arguments(**arguments)

    def set_hostname(self, hostname):
        self.add({
            "yaybu": {
                "host": hostname,
                }
            })

    def _reraise_yay_errors(self, func, *args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Error as e:
            msg = e.get_string()
            msg += "\n" + get_exception_context()
            raise ParseError(msg)

    @property
    @memoized
    def state(self):
        # FIXME: Perhaps this should be done with "create" as well????
        try:
            storage_config = self["state-storage"].as_dict()
            klass = storage_config['class']
            del storage_config['class']
        except NoMatching:
            storage_config = {}
            klass = "localfilestatestorage"

        state = StateStorageType.types.get(klass)(**storage_config)

        if self.simulate:
            state = SimulatedStateStorageAdaptor(state)

        return state

    def load_uri(self, *args, **kwargs):
        return self._reraise_yay_errors(super(Config, self).load_uri, *args, **kwargs)

    def add(self, mapping):
        return self._reraise_yay_errors(super(Config, self).add, mapping)
