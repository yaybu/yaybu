# Copyright 2013 Isotoma Limited
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

from pkg_resources import iter_entry_points

from .part import Provision

import yaybu.provisioner.resources
for ep in iter_entry_points(group='yaybu.resource', name=None):
    ep.load()

import yaybu.provisioner.providers
for ep in iter_entry_points(group='yaybu.providers', name=None):
    ep.load()

