import unittest2
import mock
from yaybu.compute import util


class TestSubRunner(unittest2.TestCase):

    @mock.patch("os.path.isfile")
    @mock.patch("os.access")
    def _create(self, where, bail, m_access, m_isfile):
        m_access.return_value = True
        m_isfile.side_effect = lambda path: path == where
        with mock.patch.dict('os.environ', {'PATH': "/path/1:/path/2"}):
            self.subrunner = util.SubRunner(
                command_name="foo",
                known_locations=["/opt/doesnotexist", "/usr/local/doge"],
                bail_if_absent=bail,
            )

    def test_exists_bail(self):
        self._create("/usr/local/doge/foo", True)
        self.assertEqual(self.subrunner.pathname, "/usr/local/doge/foo")

    def test_noexists_bail(self):
        self.assertRaises(util.SubRunnerException, self._create, "", True)

    def test_noexists_nobail(self):
        self._create("", False)
        self.assertEqual(self.subrunner.pathname, None)
