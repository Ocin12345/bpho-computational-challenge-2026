from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from task08_quantum_cryptography.final_validation import (
    _figure_package_pass,
    validate_task08_final,
)


REPOSITORY_ROOT = Path(__file__).resolve().parent.parent


class FinalAcceptanceValidationTests(unittest.TestCase):
    def test_complete_final_artifact_package_passes(self) -> None:
        report = validate_task08_final()
        self.assertTrue(report.passed)
        self.assertEqual(len(report.checks), 8)
        self.assertEqual(len({check.name for check in report.checks}), 8)

    def test_current_figure_manifest_contract(self) -> None:
        passed, detail = _figure_package_pass(REPOSITORY_ROOT)
        self.assertTrue(passed, detail)
        payload = json.loads(
            (REPOSITORY_ROOT / "figures/task08/manifest.json").read_text()
        )
        self.assertEqual(payload["figure_font_family"], "Times New Roman")
        self.assertEqual(payload["schema_version"], "task08-figure-manifest-v2")
        self.assertEqual(len(payload["files"]), 12)

    def test_missing_browser_capture_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            shutil.copytree(
                REPOSITORY_ROOT / "data/task08",
                root / "data/task08",
            )
            shutil.copytree(
                REPOSITORY_ROOT / "figures/task08",
                root / "figures/task08",
            )
            missing = root / "figures/task08/screenshots/detector_workspace_4k.png"
            missing.unlink()
            from task08_quantum_cryptography.final_validation import (
                _browser_evidence_pass,
            )

            passed, detail = _browser_evidence_pass(root)
            self.assertFalse(passed)
            self.assertIn("missing detector_workspace_4k.png", detail)


if __name__ == "__main__":
    unittest.main()
