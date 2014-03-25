
import unittest2
import mock

from yaybu.compute.image import vmware


class TestVMX(unittest2.TestCase):

    @mock.patch("os.path.exists")
    @mock.patch("__builtin__.open")
    def test_read(self, m_open, m_exists):
        m_exists.return_value = True
        vmware.VMX("/foo/bar", "vmware")
