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


from yaybu.tests import (  # noqa
    test_compute_util,
    test_changesource,
    test_compute_part,
    test_core_command,
    test_core_config,
    test_core_main,
    test_dns,
    test_heroku,
    test_loadbalancer,
    test_static,
    test_test_manifest,
    test_util_templates
)

__all__ = [m for m in list(globals()) if m.startswith("test_")]
