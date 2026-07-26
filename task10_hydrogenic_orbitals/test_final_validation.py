"""Tests for the Task 10 final artifact acceptance gate."""

from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

from task10_hydrogenic_orbitals.final_validation import (
    FinalAcceptanceCheck,
    FinalAcceptanceReport,
    _manifest_hashes_match,
    validate_task10_final,
)


class FinalAcceptanceValidationTests(unittest.TestCase):
    def test_complete_final_artifact_package_passes(self) -> None:
        report = validate_task10_final()

        self.assertTrue(
            report.passed,
            msg="; ".join(
                f"{check.name}: {check.detail}" for check in report.failed_checks
            ),
        )
        self.assertEqual(len(report.checks), 8)

    def test_manifest_hash_helper_detects_changed_and_missing_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            artifact = root / "artifact.txt"
            artifact.write_text("accepted\n", encoding="utf-8")
            digest = hashlib.sha256(artifact.read_bytes()).hexdigest()

            passed, detail = _manifest_hashes_match(
                root, {"artifact.txt": digest}
            )
            self.assertTrue(passed)
            self.assertEqual(detail, "1 digests")

            artifact.write_text("changed\n", encoding="utf-8")
            passed, detail = _manifest_hashes_match(
                root, {"artifact.txt": digest, "missing.txt": digest}
            )
            self.assertFalse(passed)
            self.assertIn("digest mismatch artifact.txt", detail)
            self.assertIn("missing missing.txt", detail)

    def test_report_exposes_failed_groups(self) -> None:
        report = FinalAcceptanceReport(
            checks=(
                FinalAcceptanceCheck("passing", True, "ok"),
                FinalAcceptanceCheck("failing", False, "detected"),
            )
        )

        self.assertFalse(report.passed)
        self.assertEqual(
            tuple(check.name for check in report.failed_checks), ("failing",)
        )


if __name__ == "__main__":
    unittest.main()
