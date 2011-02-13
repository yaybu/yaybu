import unittest
from yaybu.resource import filesystem as resource
from yaybu.provider import filesystem
import os
from yaybu.core import shell

class TestFile(unittest.TestCase):

    def setUp(self):
        if not os.path.exists("test_file"):
            os.mkdir("test_file")

    def test_template(self):
        r = resource.File(
            name="test_file/test_template.out",
            template="package://yaybu.provider/tests/template1.j2",
            template_args={"foo": "this is foo", "bar": 42}
            )
        p = filesystem.File(r, None)
        p.action_create(shell.Shell())


