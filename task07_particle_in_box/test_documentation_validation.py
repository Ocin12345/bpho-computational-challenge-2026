"""Tests for the Task 7 documentation integrity report."""

from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from task07_particle_in_box.documentation_validation import (
    DOCUMENTATION_FILENAMES,
    REPOSITORY_ROOT,
    validate_task07_documentation,
)


class DocumentationValidationTests(unittest.TestCase):
    def test_complete_documentation_passes(self) -> None:
        report = validate_task07_documentation()
        self.assertTrue(
            report.passed,
            msg="; ".join(
                f"{check.name}: {check.detail}" for check in report.failed_checks
            ),
        )
        self.assertEqual(len(report.checks), 13)
        self.assertEqual(len({check.name for check in report.checks}), 13)

    def test_missing_documentation_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            report = validate_task07_documentation(Path(temporary))
            self.assertFalse(report.passed)
            required = next(check for check in report.checks if check.name == "required_files")
            self.assertFalse(required.passed)

    def test_changed_official_digest_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            destination = root / "task07_particle_in_box"
            destination.mkdir(parents=True)
            for filename in DOCUMENTATION_FILENAMES:
                shutil.copy2(
                    REPOSITORY_ROOT / "task07_particle_in_box" / filename,
                    destination / filename,
                )
            official = destination / "OFFICIAL_REQUIREMENTS.md"
            official.write_text(
                official.read_text(encoding="utf-8").replace(
                    "330bffb2b7424cf0faada630aed39515cca32fcfee2dcf2096c218144498c667",
                    "0" * 64,
                ),
                encoding="utf-8",
            )
            report = validate_task07_documentation(root)
            self.assertFalse(report.passed)
            self.assertIn(
                "official_source_traceability",
                {check.name for check in report.failed_checks},
            )


if __name__ == "__main__":
    unittest.main()
