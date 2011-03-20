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
from yaybu.core.policy import Policy
from yaybu.core.argument import (
    String,
    Integer,
    Boolean,
    )


class Group(Resource):

    """ A resource representing a unix group.

    For example::

        Group:
            name: zope
            system: true
    """

    name = String()
    """ The name of the unix group. """

    gid = Integer()
    """ The group ID associated with the group. If this is not specified one will be chosen. """

    system = Boolean()
    """ Whether or not this is a system group. """

    password = String()
    """ The password for the group, if required """

class GroupApplyPolicy(Policy):

    """ Create the group, or ensure it has the specified attributes. """

    resource = Group
    name = "apply"
    default = True
