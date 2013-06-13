import unittest2
import os
import tempfile
import mock
import optparse

from yaybu.core.command import YaybuCmd
from yaybu.dns import Zone

class ZoneTester(Zone):
    pass


class TestDNSProvision(unittest2.TestCase):

    def _config(self, contents):
        f = tempfile.NamedTemporaryFile(delete=False)
        f.write(contents)
        f.close()
        path = os.path.realpath(f.name)
        self.addCleanup(os.unlink, path)
        return path

    def _up(self, config, *args):
        p = optparse.OptionParser()
        y = YaybuCmd(self._config(config))
        y.verbose = 2
        y.debug = True
        y.opts_up(p)
        return y.do_up(*p.parse_args(list(args)))

    def test_empty_records_list(self):
        self._up("""
            new Zone as myzone:
                    driver:
                        id: DUMMY
                        api_key: dummykey
                        api_secret: dummysecret
                    domain: example.com
                    records: []
            """)

    def __test_add_records(self):
        # FIXME
        self._up("""
            new Zone as myzone:
                    driver:
                        id: DUMMY
                        api_key: dummykey
                        api_secret: dummysecret
                    domain: example.com
                    records:
                      - name: www
                        data: 127.0.0.1
            """)

