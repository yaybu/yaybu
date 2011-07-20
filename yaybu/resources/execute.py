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
    Integer,
    Octal,
    File,
    Dict,
    List,
    )


class Execute(Resource):

    """ Execute a command. This command is not executed in a shell - if you
    want a shell, run it (for example bash -c).

    For example::

        Execute:
          name: core_packages_apt_key
          command: apt-key adv --keyserver keyserver.ubuntu.com --recv-keys ${source.key}

    A much more complex example. This shows executing a command if a checkout synchronises::

        Execute.foreach bi in ${flavour.base_images}:
          name: base-image-${bi}
          policy:
              apply:
                  when: sync
                  on: /var/local/checkouts/ci
          command: ./vmbuilder-${bi}
          cwd: /var/local/checkouts/ci
          user: root

    """

    name = String()
    """ The name of this resource. This should be unique and descriptive, and
    is used so that resources can reference each other. """

    command = String()
    """ If you wish to run a single command, then this is the command. """

    commands = List()
    """ If you wish to run multiple commands, provide a list """

    cwd = FullPath(default='/')
    """ The current working directory in which to execute the command. """

    environment = Dict()
    """

    The environment to provide to the command, for example::

        Execute:
            name: example
            command: echo $FOO
            environment:
                FOO: bar
    """

    returncode = Integer(default=0)
    """ The expected return code from the command, defaulting to 0. If the
    command does not return this return code then the resource is considered
    to be in error. """

    user = String(default="root")
    """ The user to execute the command as.
    """

    group = String(default="root")
    """ The group to execute the command as.
    """

    unless = String(default="")
    """ A command to run to determine is this execute should be actioned
    """

    creates = FullPath()
    """ The full path to a file that execution of this command creates. This
    is used like a "touch test" in a Makefile. If this file exists then the
    execute command will NOT be executed. """

    touch = FullPath()
    """ The full path to a file that yaybu will touch once this command has
    completed successfully. This is used like a "touch test" in a Makefile. If
    this file exists then the execute command will NOT be executed. """

class ExecutePolicy(Policy):

    """ Execute the the command or commands provided.

    If user or group attributes are provided the command will be run using sudo."""

    resource = Execute
    name = "execute"
    default = True
    signature = (Present("name"),
        XOR(Present("command"), Present("commands")),
        XOR(Present("creates"), Present("touch")),
        )

