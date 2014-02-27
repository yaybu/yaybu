import unittest
import os
import glob

import yaybu.tests


class TestTestManifest(unittest.TestCase):

    # Our default unittest runner in dev is nose2. This has lots of nice extras
    # like collecting stdout and showing it alongside the correct test result.

    # However in a "packed" binary build (such as py2exe) it won't be able to
    # discover tests by scanning the yaybu directory. We have to rely on
    # yaybu/tests/__init__.py importing all the tests.

    # This test asserts that yaybu/tests/__init__.py does indeed list all of
    # the tests.

    def test_test_manifest(self):
        if not os.path.exists(__file__):
            # We are probably running from inside a library.zip or similar
            # Bail out
            return

        current_manifest = dir(yaybu.tests)

        test_dir = os.path.dirname(__file__)
        for path in glob.glob(os.path.join(test_dir, "test_*.py")):
            modname = os.path.basename(path)[:-3]
            self.assertIn(modname, current_manifest)
