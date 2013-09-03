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

import stat

from yaybu.tests.provisioner_fixture import TestCase
from yaybu.core import error

test_execute_on_path = """
#!/bin/sh
touch /etc/test_execute_on_path
""".strip()

test_touches = """
#!/bin/sh
touch /etc/test_execute_touches
""".strip()


class TestExecute(TestCase):

    def test_execute_on_path(self):
        with self.chroot.open("/usr/bin/test_execute_on_path.sh", "w") as fp:
            fp.write(test_execute_on_path)
        self.chroot.chmod("/usr/bin/test_execute_on_path.sh", 0755)

        self.chroot.check_apply("""
            resources:
                - Execute:
                    name: test
                    command: test_execute_on_path.sh
                    creates: /etc/test_execute_on_path
            """)

    def test_execute_touches(self):
        """ test that command works as expected """
        with self.chroot.open("/usr/bin/test_touches.sh", "w") as fp:
            fp.write(test_touches)
        self.chroot.chmod("/usr/bin/test_touches.sh", 0755)

        self.chroot.check_apply("""
            resources:
                - Execute:
                    name: test
                    command: test_touches.sh
                    creates: /etc/test_execute_touches

            """)

    def test_command(self):
        """ test that commands works as expected """
        self.chroot.check_apply("""
            resources:
                - Execute:
                    name: test
                    command: touch /etc/foo
                    creates: /etc/foo
            """)
        self.failUnlessExists("/etc/foo")

    def test_commands(self):
        self.chroot.check_apply("""
            resources:
                - Execute:
                    name: test
                    commands:
                        - touch /etc/foo
                        - touch /etc/bar
                    creates: /etc/bar
            """)
        self.failUnlessExists("/etc/foo")
        self.failUnlessExists("/etc/bar")

    def test_cwd(self):
        """ test that cwd works as expected. """
        self.chroot.check_apply("""
            resources:
                - Execute:
                    name: test
                    command: touch foo
                    cwd: /etc
                    creates: /etc/foo
            """)
        self.failUnlessExists("/etc/foo")

    def test_environment(self):
        """ test that the environment is passed as expected. """
        self.chroot.check_apply("""
            resources:
                - Execute:
                    name: test
                    command: sh -c "touch $FOO"
                    environment:
                        FOO: /etc/foo
                    creates: /etc/foo
            """)
        self.failUnlessExists("/etc/foo")

    def test_environment_protected(self):
        self.chroot.check_apply("""
            secreted_string: /etc/foo_secret

            resources:
                - Execute:
                    name: test
                    command: sh -c "touch $FOO"
                    environment:
                        FOO: {{secreted_string}}
                    creates: /etc/foo_secret
            """)
        self.failUnlessExists("/etc/foo_secret")

    def test_returncode(self):
        """ test that the returncode is interpreted as expected. """
        self.chroot.check_apply("""
            resources:
                - Execute:
                    name: test-execute-returncode-true
                    command: /bin/true
                    touch: /test_returncode_marker_true
                - Execute:
                    name: test-execute-returncode-false
                    command: /bin/false
                    touch: /test_returncode_marker_false
                    returncode: 1
            """)

    def test_user(self):
        """ test that the user has been correctly set. """
        self.chroot.check_apply("""
            resources:
                - Execute:
                    name: test_user_change
                    command: python -c "import os; open('/foo','w').write(str(os.getuid())+'\\n'+str(os.geteuid()))"
                    user: nobody
                    creates: /foo
            """)

        with self.chroot.open("/foo") as fp:
            check_file = fp.read().split()

        self.failUnlessEqual(["65534"] * 2, check_file)

    def test_group(self):
        """ test that the group has been correctly set. """
        self.chroot.check_apply("""
            resources:
                - Execute:
                    name: test_group_change
                    command: python -c "import os; open('/foo','w').write(str(os.getgid())+'\\n'+str(os.getegid()))"
                    group: nogroup
                    creates: /foo
        """)

        with self.chroot.open("/foo") as fp:
            check_file = fp.read().split()
        self.failUnlessEqual(["65534"] * 2, check_file)

    def test_user_and_group(self):
        """ test that both user and group can be set together. """
        self.chroot.check_apply("""
            resources:
                - Execute:
                    name: test_group_change
                    command: python -c "import os; open('/foo','w').write('\\n'.join(str(x) for x in (os.getuid(),os.geteuid(),os.getgid(),os.getegid())))"
                    user: nobody
                    group: nogroup
                    creates: /foo
        """)

        with self.chroot.open("/foo") as fp:
            check_file = fp.read().split()
        self.failUnlessEqual(["65534"] * 4, check_file)

    def test_creates(self):
        """ test that the execute will not happen if the creates parameter
        specifies an existing file. """
        self.chroot.touch("/existing-file")
        self.assertRaises(error.NothingChanged, self.chroot.apply, """
            resources:
              - Execute:
                  name: test_creates
                  command: touch /existing-file
                  creates: /existing-file
            """)

    def test_touch(self):
        """ test that touch does touch a file. """
        self.chroot.check_apply("""
            resources:
             - Execute:
                 name: test_touch
                 command: whoami
                 touch: /touched-file
            """)
        self.failUnlessExists("/touched-file")

    def test_touch_present(self):
        """ test that we do not execute if the touched file exists. """
        self.chroot.touch("/touched-file")
        self.assertRaises(error.NothingChanged, self.chroot.apply, """
            resources:
             - Execute:
                 name: test_touch_present
                 command: touch /checkpoint
                 touch: /touched-file
            """)

    def test_touch_not_present(self):
        """ test that we do execute if the touched file does not exist. """
        self.chroot.check_apply("""
            resources:
             - Execute:
                 name: test_touch_not_present
                 command: touch /checkpoint
                 touch: /touched-file
            """)

        self.failUnlessExists("/checkpoint")
        self.failUnlessExists("/touched-file")

    def test_unless_true(self):
        """ test that an Execute wont execute if the unless expression
        is true """

        self.assertRaises(error.NothingChanged, self.chroot.apply, """
            resources:
              - Execute:
                  name: test
                  command: touch /test_unless_true
                  unless: /bin/true
            """)

    def test_unless_false(self):
        """ test that an Execute will execute when the unless expression
        is false """

        self.chroot.check_apply("""
            resources:
              - Execute:
                  name: test
                  command: touch /test_unless_false
                  unless: /bin/false
                  creates: /test_unless_false
            """)

        self.failUnlessExists("/test_unless_false")

    def test_umask_022(self):
        self.chroot.check_apply("""
            resources:
              - Execute:
                  name: touch
                  command: touch /test_umask_022
                  umask: 022
                  creates: /test_umask_022
            """)
        self.failUnlessExists("/test_umask_022")

        mode = stat.S_IMODE(self.chroot.stat("/test_umask_022").st_mode)
        self.failUnlessEqual(mode, 0644)

    def test_umask_002(self):
        self.chroot.check_apply("""
            resources:
              - Execute:
                  name: touch
                  command: touch /test_umask_002
                  umask: 002
                  creates: /test_umask_002
            """)
        self.failUnlessExists("/test_umask_002")

        mode = stat.S_IMODE(self.chroot.stat("/test_umask_002").st_mode)
        self.failUnlessEqual(mode, 0664)

    def test_missing_binary(self):
        self.assertRaises(error.BinaryMissing, self.chroot.apply, """
            resources:
              - Execute:
                  name: test_missing_binary
                  command: this_binary_definitely_doesnt_exist
            """)

    def test_missing_binary_absolute(self):
        self.assertRaises(error.BinaryMissing, self.chroot.apply, """
            resources:
              - Execute:
                  name: test_missing_binary_absolute
                  command: /this_binary_definitely_doesnt_exist
            """)

    def test_missing_user_and_group(self):
        self.chroot.check_apply("""
            resources:
              - Group:
                  name: test
              - User:
                  name: test
              - Execute:
                  name: test-execute
                  command: touch /test_missing_user
                  creates: /test_missing_user
                  unless: /bin/false
                  user: test
                  group: test
            """)

        self.failUnlessExists("/test_missing_user")


