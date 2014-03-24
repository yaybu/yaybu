import unittest2
import mock
from yaybu.compute import util

class TestSubRunner(unittest2.TestCase):

    @mock.patch("os.path.exists")
    def setUp(self, m_exists):
        m_exists.side_effect = lambda path: path == '/usr/local/doge/foo'
        with mock.patch.dict('os.environ', {'PATH': "/path/1:/path/2"}):

            class MockSubRunner(util.SubRunner):

                @classmethod
                def command_name(klass):
                    return "foo"

                @classmethod
                def known_locations(klass):
                    return [
                        "/opt/doesnotexist",
                        "/usr/local/doge",
                    ]

        self.subrunner = MockSubRunner()

    def test_location(self):
        self.assertEqual(self.subrunner.command_path, "/usr/local/doge/foo")

