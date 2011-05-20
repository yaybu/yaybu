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
    FullPath,
    String,
    Boolean,
    Integer,
    )


class Service(Resource):

    """ This represents service startup and shutdown via an init daemon. """

    name = String()
    """ A unique name representing an initd service.

    This would normally match the name as it appears in /etc/init.d.
    """

    priority = Integer(default=99)
    """ Priority of the service within the boot order.

    This attribute will have no effect when using a dependency or event based
    init.d subsystem like upstart or systemd. """

    start = String()
    """ A command that when executed will start the service.

    If not provided, the provider will use the default service start invocation
    for the init.d system in use.
    """

    stop = String()
    """ A command that when executed will start the service.

    If not provided, the provider will use the default service stop invocation
    for the init.d system in use.
    """

    restart = String()
    """ A command that when executed will restart the service.

    If not provided, the provider will use the default service restart invocation
    for the init.d system in use. If it is not possible to automatically determine
    if the restart script is avilable the service will be stopped and started instead.
    """

    reconfig = String()
    """ A command that when executed will make the service reload its
    configuration file. """

    pidfile = FullPath()
    """ Where the service creates its pid file.

    This can be provided instead of a status command as an alternative way of checking if
    a service is running or not.
    """


class ServiceStartPolicy(Policy):

    """ Start a service if it isn't running """

    resource = Service
    name = "start"
    default = True
    signature = (
        Present("name"),
        NAND(Present("status"), Present("pidfile")),
        )


class ServiceStopPolicy(Policy):

    """ Stop a service if it is running """

    resource = Service
    name = "stop"
    signature = (
        Present("name"),
        NAND(Present("status"), Present("pidfile")),
        )


class ServiceRestartPolicy(Policy):

    """ Restart a service

    If a service isn't running it will just be started instead.
    """

    resource = Service
    name = "restart"
    signature = (
        Present("name"),
        NAND(Present("status"), Present("pidfile")),
        )


class ServiceReloadPolicy(Policy):

    """ Get the service to reload its configuration

    If a service isn't running it will just be started instead.
    """

    resource = Service
    name = "reconfig"
    signature = (
        Present("name"),
        NAND(Present("status"), Present("pidfile")),
        )

