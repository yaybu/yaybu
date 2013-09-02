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

from yaybu.provisioner.resource import Resource
from yaybu.core.policy import Policy, Present
from yaybu.core.argument import (
    Property,
    FullPath,
    String,
    Integer,
    Octal,
    File,
    Dict,
    )


class Patch(Resource):

    """
    A provider for this resource will copy a source file from the target system
    and apply a patch to it.

    For example::

        - Patch:
            target: /output
            source: /output
            patch: localfile

    """

    name = Property(FullPath)
    """The full path to the file this resource represents."""

    source = Property(FullPath)
    """ The full path to a file to copy to target and patch """

    patch = Property(File)

    strip = Property(Integer, default=0)
    """ Strip the smallest prefix containing ``strip`` leading slashes from
    each file name found in the patch. """

    owner = Property(String, default="root")
    """A unix username or UID who will own created objects. An owner that
    begins with a digit will be interpreted as a UID, otherwise it will be
    looked up using the python 'pwd' module."""

    group = Property(String, default="root")
    """A unix group or GID who will own created objects. A group that begins
    with a digit will be interpreted as a GID, otherwise it will be looked up
    using the python 'grp' module."""

    mode = Property(Octal, default="644")
    """A mode representation as an octal. This can begin with leading zeros if
    you like, but this is not required. DO NOT use yaml Octal representation
    (0o666), this will NOT work."""

    template_args = Property(Dict, default={})
    """The arguments passed to the template."""


class PatchApplyPolicy(Policy):

    """ Apply a patch.

    You must provide a target.
    """

    resource = Patch
    name = "apply"
    default = True
    signature = (Present("name"),
                 )

