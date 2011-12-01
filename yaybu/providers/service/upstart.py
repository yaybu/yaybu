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
from collections import namedtuple

from yaybu.core import provider
from yaybu.providers.service import utils
from yaybu import resources

UpstartInfo = namedtuple('UpstartInfo', ['name', 'goal', 'status'])

class _UpstartServiceMixin(utils._ServiceMixin):

    features = ["restart", ]

    def _parse_line(self, line):
        """
        Converts a line of information from /sbin/status into a tuple of (name,
        goal, status). Any PID information is discared as we don't need it.

        Has to deal with strings like::

            hwclock stop/waiting
            ssh start/running, process 4931
            network-interface-security (network-manager) start/running
        """
        name, status = line.split(" ", 1)
        if status.startswith("("):
            instance, status = status.split(") ", 1)
            instance = instance.lstrip("(")
        else:
           instance = name
        goal, status = status.split("/", 1)
        if "," in status:
            status, _ = status.split(",", 1)
        return UpstartInfo(instance, goal, status)

    def _parse_status_output(self, statusblob):
        """
        Yields status information from the output of /sbin/status
        
        Can cope with multiple instances of a job like this::

            network-interface-security (network-manager) start/running
            network-interface-security (network-interface/eth0) start/running
            network-interface-security (network-interface/lo) start/running
            network-interface-security (networking) start/running
        """
        for line in statusblob.strip().split("\n"):
            if not line.strip():
                continue
            yield self._parse_line(line)

    def status(self, context):
        rv, stdout, stderr = context.shell.execute(["/sbin/status", self.resource.name], exceptions=False, passthru=True)
        if rv != 0:
            raise error.CommandError("Got exit code of %d whilst trying to determine status" % rv)

        if "Unknown job" in stderr:
            raise error.CommandError("Upstart does not know about this job")

        statuses = list(self._parse_status_output(stdout))

        if len(statuses) == 0:
            raise error.CommandError("Upstart returned no information for the job")

        if len(statuses) > 1:
            raise error.CommandError("The job has multiple statuses. This is currently not supported in Yaybu recipes.")

        try:
            return dict(start="running", stop="not-running")[statuses[0].goal]
        except KeyError:
            raise error.CommandError("The job has an unexpected goal of '%s'" % statuses[0].goal)

    @classmethod
    def isvalid(cls, policy, resource, yay):
        if not super(_UpstartServiceMixin, cls).isvalid(policy, resource, yay):
            return False
        if getattr(resource, policy.name):
            return False
        return os.path.exists("/sbin/start") and os.path.exists("/etc/init/%s.conf" % resource.name)

    def get_command(self, action):
        return ["/sbin/" + action, self.resource.name]


class Start(_UpstartServiceMixin, utils._Start, provider.Provider):
    pass


class Stop(_UpstartServiceMixin, utils._Stop, provider.Provider):
    pass


class Restart(_UpstartServiceMixin, utils._Restart, provider.Provider):
    pass


