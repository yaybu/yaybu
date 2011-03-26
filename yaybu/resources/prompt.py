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
    )
from yaybu.core.argument import (
    String,
    Integer,
    )

class Prompt(Resource):

    """ Ask a question of the operator. This is useful if manual steps are
    required as part of implementing a configuration. For example, changes to
    off-system web interfaces or databases may be required as part of applying
    a change. """

    name = String()
    """ A unique descriptive name for the resource. """

    question = String()
    """ The question to ask the operator. """

class PromptPolicy(Policy):

    """ Prompt the operator.

    The value of the question attribute will be displayed to the operator and
    deployment will not continue until they acknowledge the prompt."""

    resource = Prompt
    name = "prompt"
    default = True
    signature = (
        Present("name"),
        Present("question"),
        )
