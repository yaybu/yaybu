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

try:
    from fixtures import Fixture as BaseFixture
except ImportError:
    class BaseFixture(object):
        """
        I am a Fixture compatible with the fixtures API by Robert Collins
        If the fixtures package is installed I won't be used.
        """
        def getDetails(self):
            return {}


class Fixture(BaseFixture):

    """ A base class for Fixtures that providing virtual environments to deploy configuration in.

    This base class is abstract and provides no concrete implementations. For a simple implementation
    of this interface see :py:class:`~yaybu.harness.fakechroot.FakeChrootFixture`.
    """

    def exists(self, path):
        """ Checks whether or not a path exists in the target """
        raise NotImplementedError(self.exists)

    def isdir(self, path):
        """ Checks whether or not a path is a directory in the target """
        raise NotImplementedError(self.isdir)

    def mkdir(self, path):
        """ Creates a directory in the target """
        raise NotImplementedError(self.mkdir)

    def open(self, path, mode='r'):
        """ Opens a file in the target """
        raise NotImplementedError(self.open)

    def touch(self, path):
        """ Ensures that a file exists in the target """
        raise NotImplementedError(self.touch)

    def chmod(self, path, mode):
        """ Change the permissions of a path in the target """
        raise NotImplementedError(self.chmod)

    def readlink(self, path):
        """ Return a string containing the path that a symbolic link points to """
        raise NotImplementedError(self.readlink)

    def symlink(self, source, dest):
        """ Create a symbolic link pointing to source at dest """
        raise NotImplementedError(self.symlink)

    def stat(self, path):
        """ Perform the equivalent of the a stat() system call on the given path """
        raise NotImplementedError(self.stat)

