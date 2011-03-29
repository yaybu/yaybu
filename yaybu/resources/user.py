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
    FullPath,
    Integer,
    Octal,
    File,
    Dict,
    Boolean,
    List,
    )


class User(Resource):

    """ A resource representing a UNIX user in the password database. The underlying implementation currently uses the "useradd" and "usermod" commands to implement this resource.

    This resource can be used to create, change or delete UNIX users.

    For example::

        User:
          name: django
          fullname: Django Software Owner
          home: /var/local/django
          system: true
          disabled-password: true

    """

    name = String()
    """ The username this resource represents. """

    password = String()
    """ The encrypted password, as returned by crypt(3). You should make sure
    this password respects the system's password policy. """

    fullname = String()
    """ The comment field for the password file - generally used for the user's full name. """

    home = FullPath()
    """ The full path to the user's home directory. """

    uid = Integer()
    """ The user identifier for the user. This must be a non-negative integer. """

    gid = Integer()
    """ The group identifier for the user. This must be a non-negative integer. """

    group = String()
    """ The primary group for the user, if you wish to specify it by name. """

    groups = List()
    """ A list of supplementary groups that the user should be a member of. """

    append = Boolean(default=True)
    """ A boolean that sets how to apply the groups a user is in. If true then yaybu will
    add the user to groups as needed but will not remove a user from a group. If false then yaybu will replace
    all groups the user is a member of. Thus if a process outside of yaybu adds you to a group,
    the next deployment would remove you again. """

    system = Boolean(default=True) # has no effect on modification, only creation
    """ A boolean representing whether this user is a system user or not. This only takes effect on
    creation - a user cannot be changed into a system user once created
    without deleting and recreating the user. """

    shell = FullPath(default="/bin/bash")
    """ The full path to the shell to use. """

    disabled_password = Boolean(default=False)
    """ A boolean for whether the password is locked for this account. """

    disabled_login = Boolean(default=False)
    """ A boolean for whether this entire account is locked or not. """


class UserApplyPolicy(Policy):

    """ Create or change the specified user.

    It might not be possible to apply some changes to existing users, for example
    the systeam attribute only makes sense at the point a user is created.
    """

    resource = User
    name = "apply"
    default = True


class UserRemovePolicy(Policy):

    """ Remove an existing user. This is not recommended in general - you
    should lock existing accounts instead to preserve file ownership metadata
    information. """

    resource = User
    name = "remove"
    default = False
