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

""" Resources dealing with filesystem objects other than files. """

from yaybu.core.resource import Resource
from yaybu.core.policy import (Policy,
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
    )

class Special(Resource):

    """ A special file, as created by mknod. """

    name = FullPath()
    """ The full path to the special file on disk. """

    owner = String(default="root")
    """ The unix user who should own this special file. """

    group = String(default="root")
    """ The unix group who should own this special file. """

    mode = Octal(default=0644)
    """ The octal representation of the permissions for this special file. """

    type = String(default="fifo")
    """ One of the following strings:

      block
        create a block (buffered) special file
      character
        create a character (unbuffered) special file
      fifo
        create a fifo

    It defaults to fifo
    """

    major = Integer()
    """ The major number for the special file. If the type of the special file
    is block or character, then this must be specified. """

    minor = Integer()
    """ The minor number for the special file. If the type of the special file
    is block or character, then this must be specified. """

class SpecialAppliedPolicy(Policy):

    """ Ensure a block or character special file exists """

    name = "apply"
    default = True
    signature = (Present("name"),
                 Present("owner"),
                 Present("group"),
                 Present("mode"),
                 Present("type"),
                 Present("major"),
                 Present("minor"),
                 )


class SpecialRemovedPolicy(Policy):

    """ If the special file specified exists, remove it.

    You should only specify the special file to remove, the other fields are
    not needed """

    name = "remove"
    default = False
    signature = (Present("name"),
                 Absent("owner"),
                 Absent("group"),
                 Absent("mode"),
                 Absent("type"),
                 Absent("major"),
                 Absent("minor"),
                 )

