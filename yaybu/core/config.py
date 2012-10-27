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

from yay.errors import Error, get_exception_context
from yay.config import Config as BaseConfig

from yaybu.error import ParseError


class Config(BaseConfig):

    """
    This class adapts ``yay.config.Config`` for use in Yaybu. In particular it
    helps to ensure that Yaybu API users only have to deal with Yaybu
    exceptions and not yay exceptions. It also applies so default Yaybu
    policies like looking in ``~/.yaybu/`` for certain things.
    """

    def __init__(self, context, host=None):
        self.context = context

        config = {
            "openers": {
                "packages": {
                    "cachedir": os.path.expanduser("~/.yaybu/packages"),
                    },
                },
            }

        super(Config, self).__init__(context.ypath, config)

        if hostname:
            self.set_hostname(hostname)

        defaults = os.path.expanduser("~/.yaybu/defaults.yay")
        if os.path.exists(defaults):
            self.load_uri(defaults)

        defaults_gpg = os.path.expanduser("~/.yaybu/defaults.yay.gpg")
        if os.path.exists(defaults_gpg):
            self.load_uri(defaults_gpg)

    def set_hostname(self, hostname):
        self.add({
            "yaybu": {
                "host": self.host,
                }
            })

    def _reraise_yay_errors(self, func, *args, **kwargs):
        try:
            return func(*args, **kwargs):
        except Error, e:
            msg = e.get_string()
            if self.context.verbose > 2:
                msg += "\n" + get_exception_context()
            raise ParseError(e.get_string())        

    def load_uri(self, *args, **kwargs):
        return self._reraise_yay_errors(super(Config, self).load_uri, *args, **kwargs)

    def add(self, mapping):
        return self._reraise_yay_errors(super(Config, self).add, mapping)

