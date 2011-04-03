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
        """ test that command works as expected """

    def test_commands(self):
        """ test that commands works as expected """

    def test_cwd(self):
        """ test that cwd works as expected. """

    def test_environment(self):
        """ test that the environment is passed as expected. """

    def test_returncode(self):
        """ test that the returncode is interpreted as expected. """

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

