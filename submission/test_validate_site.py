"""Regression checks for missing assets in a downloaded project."""

import tempfile
import unittest
from pathlib import Path

from submission.validate_site import validate_site


class SiteDependenciesTests(unittest.TestCase):
    def test_reports_missing_asset_and_accepts_query_strings_and_data_uris(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            assets = root / "site/assets"
            assets.mkdir(parents=True)
            (root / "site/index.html").write_text(
                '<link href="assets/style.css?v=2"><img src="missing.png">'
            )
            (assets / "style.css").write_text(
                'a {background: url("data:image/svg+xml,%3Csvg%3E%3C/svg%3E")} '
                'b {background: url("../image%20one.svg#shape")}'
            )
            (root / "site/image one.svg").write_text("<svg/>")
            count, failures = validate_site(root)
            self.assertEqual(count, 3)
            self.assertEqual(failures, ["site/index.html -> missing.png"])
            (root / "site/missing.png").write_bytes(b"image")
            self.assertEqual(validate_site(root)[1], [])

    def test_checks_module_imports_and_worker_urls(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            assets = root / "site/assets"
            assets.mkdir(parents=True)
            (root / "site/index.html").write_text('<script src="assets/main.js"></script>')
            (assets / "main.js").write_text(
                'import {run} from "./engine.js"; '
                'new Worker(new URL("./worker.js", import.meta.url));'
            )
            self.assertEqual(len(validate_site(root)[1]), 2)
            (assets / "engine.js").write_text("export const run = () => {};")
            (assets / "worker.js").write_text("// worker")
            self.assertEqual(validate_site(root)[1], [])


if __name__ == "__main__":
    unittest.main()
