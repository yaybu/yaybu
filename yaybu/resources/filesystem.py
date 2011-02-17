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
from yaybu.core.policy import (Policy,
                               Absent,
                               Present,
                               XOR,
                               NAND)

from yaybu.core.argument import (
    String,
    Integer,
    Octal,
    File,
    Dict,
    )

class File(Resource):

    """ A provider for this resource will create or amend an existing file to the following specification:

    """

    name = String()
    owner = String()
    group = String()
    mode = Octal()
    static = File()
    template = File()
    template_args = Dict(default={})
    backup = String()
    dated_backup = String()

class FileAppliedPolicy(Policy):

    resource = File
    name = "applied"
    default = True
    signature = (Present("name"),
                 NAND(Present("template"),
                      Present("static")),
                 NAND(Present("backup"),
                      Present("dated_backup")),
                 )

class FileRemovePolicy(Policy):

    resource = File
    name = "removed"
    default = False
    signature = (Present("name"),
                 Absent("owner"),
                 Absent("group"),
                 Absent("mode"),
                 Absent("static"),
                 Absent("template"),
                 Absent("template_args"),
                 NAND(Present("backup"),
                      Present("dated_backup")),
                 )

class Directory(Resource):
    name = String()
    owner = String()
    group = String()
    mode = Octal()

class DirectoryAppliedPolicy(Policy):
    resource = Directory
    name = "applied"
    default = True
    signature = (Present("name"),
                 Present("owner"),
                 Present("group"),
                 Present("mode"),
                 )

class DirectoryRemovedPolicy(Policy):
    resource = Directory
    name = "removed"
    default = False
    signature = (Present("name"),
                 Absent("owner"),
                 Absent("group"),
                 Absent("mode"),
                 )

class DirectoryRemovedRecursivePolicy(Policy):
    resource = Directory
    name = "removed-recursive"
    default = False
    signature = (Present("name"),
                 Absent("owner"),
                 Absent("group"),
                 Absent("mode"),
                 )

class Link(Resource):
    name = String()
    owner = String()
    group = String()
    to = String()
    mode = Octal()

class LinkAppliedPolicy(Policy):
    resource = Link
    name = "applied"
    default = True
    signature = (
        Present("name"),
        Present("to"),
        )

class LinkRemovedPolicy(Policy):
    name = "applied"
    default = False
    signature = (
        Present("name"),
        Absent("to"),
        )

class Special(Resource):
    name = String()
    owner = String()
    group = String()
    mode = Octal()
    type_ = String()
    major = Integer()
    minor = Integer()

class SpecialAppliedPolicy(Policy):
    name = "applied"
    default = True
    signature = (Present("name"),
                 Present("owner"),
                 Present("group"),
                 Present("mode"),
                 Present("type_"),
                 Present("major"),
                 Present("minor"),
                 )

class SpecialRemovedPolicy(Policy):
    name = "removed"
    default = False
    signature = (Present("name"),
                 Absent("owner"),
                 Absent("group"),
                 Absent("mode"),
                 Absent("type_"),
                 Absent("major"),
                 Absent("minor"),
                 )
