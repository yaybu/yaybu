import unittest
import pkgutil
import json
import os
import glob


class TestTestManifest(unittest.TestCase):

    def test_test_manifest(self):
        # In order for test discovery on Windows and OSX we need a list of modules to inspect
        # At the same time we don't want  to manually maintain that list
        current_manifest = json.loads(pkgutil.get_data("yaybu.tests", "manifest.json"))

        test_dir = os.path.dirname(__file__)
        manifest_path = os.path.join(test_dir, "manifest.json")
        if not os.path.exists(manifest_path):
            # We are probably running from inside a library.zip or similar
            # Bail out
            return

        manifest = []
        for path in glob.glob(os.path.join(test_dir, "test_*.py")):
            manifest.append(os.path.relpath(path, test_dir)[:-3])

        if current_manifest != manifest:
            with open(manifest_path, "w") as fp:
                json.dump(manifest, fp)
            assert False, "Manifest is stale"
