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
    Octal,
    File,
    Dict,
    )


class Execute(Resource):

    name = String()
    command = String()
    cwd = String()
    environment = Dict()
    returncode = Integer()

    user = String()
    group = String()

    creates = String()


class ExecutePolicy(Policy):

    resource = Execute
    name = "execute"
    default = True
