"""Tests for the Task 7 final artifact acceptance gate."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from task07_particle_in_box.final_validation import validate_task07_final
from task07_particle_in_box.generate_task07_report_manifest import (
    REPORT_FILENAMES,
    generate_report_manifest,
)


class FinalAcceptanceValidationTests(unittest.TestCase):
    def test_complete_final_artifact_package_passes(self) -> None:
        report = validate_task07_final()
        self.assertTrue(
            report.passed,
            msg="; ".join(
                f"{check.name}: {check.detail}" for check in report.failed_checks
            ),
        )
        self.assertEqual(len(report.checks), 8)

    def test_report_manifest_rejects_a_missing_report(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            for filename in REPORT_FILENAMES[:-1]:
                (directory / filename).write_text("placeholder", encoding="utf-8")
            with self.assertRaises(FileNotFoundError):
                generate_report_manifest(directory)

    def test_current_report_manifest_contract(self) -> None:
        manifest = json.loads(
            Path("reports/task07/manifest.json").read_text(encoding="utf-8")
        )
        self.assertEqual(len(manifest["files"]), 3)
        self.assertEqual(manifest["pdf"]["pages"], 4)
        self.assertEqual(
            manifest["accessibility"]["semantic_alternative"],
            "particle_in_box_uncertainty_accessible.md",
        )


if __name__ == "__main__":
    unittest.main()
