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

# Modules which have changed since python2.6 and we depend on a new feature

import zipfile


# Python2.7 introduced context manager support for ZipFile
if not hasattr(zipfile.ZipFile, "__exit__"):
    class ZipFile(zipfile.ZipFile):
        def __enter__(self):
            return self
        def __exit__(self, type, value, traceback):
            self.close()
else:
    ZipFile = zipfile.ZipFile

