import os, shutil

from yaybutest.utils import TestCase
from yaybu.util import sibpath


class TestExecute(TestCase):

    def test_execute_on_path(self):
        src = sibpath(__file__, os.path.join("..", "..", "files"))
        dst = os.path.join(self.chroot_path, "tmp", "files")
        shutil.copytree(src, dst)

        self.check_apply("""
            resources:
                - Execute:
                    name: test
                    command: test_execute_on_path.sh
            """)

    def test_execute_touches(self):
        """ test that command works as expected """
        src = sibpath(__file__, os.path.join("..", "..", "files"))
        dst = os.path.join(self.chroot_path, "tmp", "files")
        shutil.copytree(src, dst)

        self.check_apply("""
            resources:
                - Execute:
                    name: test
                    command: test_touches.sh
                    creates: /etc/test_execute_touches

            """)

    def test_command(self):
        """ test that commands works as expected """
        self.check_apply("""
            resources:
                - Execute:
                    name: test
                    command: touch /etc/foo
            """)
        self.failUnlessExists("/etc/foo")

    def test_commands(self):
        self.check_apply("""
            resources:
                - Execute:
                    name: test
                    commands:
                        - touch /etc/foo
                        - touch /etc/bar
            """)
        self.failUnlessExists("/etc/foo")
        self.failUnlessExists("/etc/bar")

    def test_cwd(self):
        """ test that cwd works as expected. """
        self.check_apply("""
            resources:
                - Execute:
                    name: test
                    command: touch foo
                    cwd: /etc
            """)
        self.failUnlessExists("/etc/foo")

    def test_environment(self):
        """ test that the environment is passed as expected. """
        self.check_apply("""
            resources:
                - Execute:
                    name: test
                    command: sh -c "touch $FOO"
                    environment:
                        FOO: /etc/foo
            """)
        self.failUnlessExists("/etc/foo")

    def test_returncode(self):
        """ test that the returncode is interpreted as expected. """
        self.check_apply("""
            resources:
                - Execute:
                    name: test-true
                    command: /bin/true
            """)

        self.check_apply("""
            resources:
                - Execute:
                    name: test-false
                    command: /bin/false
                    returncode: 1
            """)

    def test_user(self):
        """ test that the user has been correctly set. """
        self.check_apply("""
            resources:
                - Execute:
                    name: test_user_change
                    command: python -c "import os; open('/foo','w').write(str(os.getuid())+'\\n'+str(os.geteuid()))"
                    user: nobody
            """)

        check_file = open(self.enpathinate("/foo")).read().split()
        self.failUnlessEqual(["65534"] * 2, check_file)

    def test_group(self):
        """ test that the group has been correctly set. """
        self.check_apply("""
            resources:
                - Execute:
                    name: test_group_change
                    command: python -c "import os; open('/foo','w').write(str(os.getgid())+'\\n'+str(os.getegid()))"
                    group: nogroup
        """)

        check_file = open(self.enpathinate("/foo")).read().split()
        self.failUnlessEqual(["65534"] * 2, check_file)

    def test_user_and_group(self):
        """ test that both user and group can be set together. """
        self.check_apply("""
            resources:
                - Execute:
                    name: test_group_change
                    command: python -c "import os; open('/foo','w').write('\\n'.join(str(x) for x in (os.getuid(),os.geteuid(),os.getgid(),os.getegid())))"
                    user: nobody
                    group: nogroup
        """)

        check_file = open(self.enpathinate("/foo")).read().split()
        self.failUnlessEqual(["65534"] * 4, check_file)

    def test_creates(self):
        """ test that the execute will not happen if the creates parameter
        specifies an existing file. """

    def test_touch(self):
        """ test that touch does touch a file. """

    def test_touch_present(self):
        """ test that we do not execute if the touched file exists. """

    def test_touch_not_present(self):
        """ test that we do execute if the touched file does not exist. """

    def test_unless_true(self):
        """ test that an Execute wont execute if the unless expression
        is true """

        rv = self.apply("""
            resources:
              - Execute:
                  name: test
                  command: touch /test_unless_true
                  unless: /bin/true
            """)

        self.failUnlessEqual(rv, 255)

    def test_unless_false(self):
        """ test that an Execute will execute when the unless expression
        is false """

        self.check_apply("""
            resources:
              - Execute:
                  name: test
                  command: touch /test_unless_false
                  unless: /bin/false
            """)

        self.failUnlessExists("/test_unless_false")

