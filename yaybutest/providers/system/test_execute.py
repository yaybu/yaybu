from yaybutest.utils import TestCase

class TestExecute(TestCase):

    def test_execute_on_path(self):
        self.apply("""
            resources:
                - Execute:
                    name: test
                    command: test_execute_on_path.sh
            """)

