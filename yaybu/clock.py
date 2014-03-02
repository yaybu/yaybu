# Copyright 2013 Isotoma Limited
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

from __future__ import absolute_import
import datetime

import gevent

from yay import ast
from yaybu import base, error


class Clock(base.GraphExternalAction):

    """
    This unit provides a clock source. It is intended that there will be a
    single clocksource at ``yaybu.now``::

        if yaybu.now.day == 'sunday':
          new Provisioner as hello:
            server:
              fqdn: localhost
            resources: []
    """

    anchor = None

    def __init__(self):
        super(Clock, self).__init__(ast.PythonDict({}))

    def _run(self, change_mgr):
        while True:
            with change_mgr.changeset() as cs:
                cs.bust(self.apply)
            gevent.sleep(1)

    def listen(self, change_mgr):
        return gevent.spawn(self._run, change_mgr)

    def test(self):
        pass

    def _get_key(self, key):
        self.wait(self.apply)
        if key in ("year", "month", "day", "hour", "minute", "second", "microsecond", ):
            l = ast.Literal(getattr(self._apply_time, key))
            l.parent = self
            return l
        raise NoMatching("No such key '%s'" % key)

    def keys(self):
        return ()

    def apply(self):
        self._apply_time = datetime.datetime.now()
