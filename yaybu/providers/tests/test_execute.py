import os, shutil

from yaybu.harness import FakeChrootTestCase
from yaybu.util import sibpath
from yaybu.core import error

test_execute_on_path = """
#!/bin/sh
touch /etc/test_execute_on_path
""".strip()

test_touches = """
#!/bin/sh
touch /etc/test_execute_touches
""".strip()


class TestExecute(FakeChrootTestCase):

    def test_execute_on_path(self):
        with self.fixture.open("/usr/bin/test_execute_on_path.sh", "w") as fp:
            fp.write(test_execute_on_path)
        self.fixture.chmod("/usr/bin/test_execute_on_path.sh", 0755)

        self.fixture.check_apply("""
            resources:
                - Execute:
                    name: test
                    command: test_execute_on_path.sh
                    creates: /etc/test_execute_on_path
            """)

    def test_execute_touches(self):
        """ test that command works as expected """
        with self.fixture.open("/usr/bin/test_touches.sh", "w") as fp:
            fp.write(test_touches)
        self.fixture.chmod("/usr/bin/test_touches.sh", 0755)

        self.fixture.check_apply("""
            resources:
                - Execute:
                    name: test
                    command: test_touches.sh
                    creates: /etc/test_execute_touches

            """)

    def test_command(self):
        """ test that commands works as expected """
        self.fixture.check_apply("""
            resources:
                - Execute:
                    name: test
                    command: touch /etc/foo
                    creates: /etc/foo
            """)
        self.failUnlessExists("/etc/foo")

    def test_commands(self):
        self.fixture.check_apply("""
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
        self.fixture.check_apply("""
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
        self.fixture.check_apply("""
            resources:
                - Execute:
                    name: test
                    command: sh -c "touch $FOO"
                    environment:
                        FOO: /etc/foo
                    creates: /etc/foo
            """)
        self.failUnlessExists("/etc/foo")

    def test_returncode(self):
        """ test that the returncode is interpreted as expected. """
        self.fixture.check_apply("""
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
        self.fixture.check_apply("""
            resources:
                - Execute:
                    name: test_user_change
                    command: python -c "import os; open('/foo','w').write(str(os.getuid())+'\\n'+str(os.geteuid()))"
                    user: nobody
                    creates: /foo
            """)

        with self.fixture.open("/foo") as fp:
            check_file = fp.read().split()

        self.failUnlessEqual(["65534"] * 2, check_file)

    def test_group(self):
        """ test that the group has been correctly set. """
        self.fixture.check_apply("""
            resources:
                - Execute:
                    name: test_group_change
                    command: python -c "import os; open('/foo','w').write(str(os.getgid())+'\\n'+str(os.getegid()))"
                    group: nogroup
                    creates: /foo
        """)

        with self.fixture.open("/foo") as fp:
            check_file = fp.read().split()
        self.failUnlessEqual(["65534"] * 2, check_file)

    def test_user_and_group(self):
        """ test that both user and group can be set together. """
        self.fixture.check_apply("""
            resources:
                - Execute:
                    name: test_group_change
                    command: python -c "import os; open('/foo','w').write('\\n'.join(str(x) for x in (os.getuid(),os.geteuid(),os.getgid(),os.getegid())))"
                    user: nobody
                    group: nogroup
                    creates: /foo
        """)

        with self.fixture.open("/foo") as fp:
            check_file = fp.read().split()
        self.failUnlessEqual(["65534"] * 4, check_file)

    def test_creates(self):
        """ test that the execute will not happen if the creates parameter
        specifies an existing file. """
        self.fixture.touch("/existing-file")
        self.fixture.check_apply("""
            resources:
              - Execute:
                  name: test_creates
                  command: touch /existing-file
                  creates: /existing-file
            """, expect=error.NothingChanged.returncode)

    def test_touch(self):
        """ test that touch does touch a file. """
        self.fixture.check_apply("""
            resources:
             - Execute:
                 name: test_touch
                 command: whoami
                 touch: /touched-file
            """)
        self.failUnlessExists("/touched-file")

    def test_touch_present(self):
        """ test that we do not execute if the touched file exists. """
        self.fixture.touch("/touched-file")
        self.fixture.check_apply("""
            resources:
             - Execute:
                 name: test_touch_present
                 command: touch /checkpoint
                 touch: /touched-file
            """, expect=254)

        self.failIfExists("/checkpoint")

    def test_touch_not_present(self):
        """ test that we do execute if the touched file does not exist. """
        self.fixture.check_apply("""
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

        rv = self.fixture.apply("""
            resources:
              - Execute:
                  name: test
                  command: touch /test_unless_true
                  unless: /bin/true
            """)

        self.failUnlessEqual(rv, 254)

    def test_unless_false(self):
        """ test that an Execute will execute when the unless expression
        is false """

        self.fixture.check_apply("""
            resources:
              - Execute:
                  name: test
                  command: touch /test_unless_false
                  unless: /bin/false
                  creates: /test_unless_false
            """)

        self.failUnlessExists("/test_unless_false")

