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

from yaybu.core import provider
from yaybu.core import error
from yaybu import resources

class Prompt(provider.Provider):

    policies = (resources.prompt.PromptPolicy,)

    @classmethod
    def isvalid(self, *args, **kwargs):
        return super(Prompt, self).isvalid(*args, **kwargs)

    def apply(self, shell):

        raw_input(self.resource.question)
