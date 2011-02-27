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

