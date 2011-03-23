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

from yaybu.core.resource import Resource
from yaybu.core.policy import (
    Policy,
    Absent,
    Present,
    XOR,
    NAND)

from yaybu.core.argument import (
    String,
    Boolean,
    Integer,
    Octal,
    File,
    Dict,
    List,
    )


class Service(Resource):

    name = String()
    enabled = Boolean()

    start = String()
    stop = String()
    restart = String()
    reconfig = String()
    status = String()

    actions = ["nothing", "start", "stop", "restart", "reload"]


class ServiceStartPolicy(Policy):

    """ Start a service if it isn't running """

    resource = Service
    name = "start"
    default = True
    signature = (Present("name"), )


class ServiceStopPolicy(Policy):

    """ Stop a service if it is running """

    resource = Service
    name = "stop"
    signature = (Present("name"), )


class ServiceRestartPolicy(Policy):

    """ Restart a service

    If a service isn't running it will just be started instead.
    """

    resource = Service
    name = "restart"
    signature = (Present("name"), )


class ServiceReloadPolicy(Policy):

    """ Get the service to reload its configuration

    If a service isn't running it will just be started instead.
    """

    resource = Service
    name = "reconfig"
    signature = (Present("name"), )

