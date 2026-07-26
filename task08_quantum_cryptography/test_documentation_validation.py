"""Tests for Task 8 explanatory-documentation integrity."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from task08_quantum_cryptography.documentation_validation import (
    DOCUMENTATION_FILENAMES,
    DocumentationCheck,
    DocumentationValidationReport,
    validate_task08_documentation,
)


class DocumentationValidationTests(unittest.TestCase):
    def test_complete_documentation_passes(self) -> None:
        report = validate_task08_documentation()
        self.assertTrue(report.passed)
        self.assertEqual(len(report.checks), 10)
        self.assertEqual(len({check.name for check in report.checks}), 10)

    def test_missing_documentation_is_reported_without_crashing(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            report = validate_task08_documentation(Path(temporary))
            self.assertFalse(report.passed)
            required = next(check for check in report.checks if check.name == "required_files")
            self.assertIn(f"0/{len(DOCUMENTATION_FILENAMES)}", required.detail)

    def test_report_and_check_contracts_reject_invalid_values(self) -> None:
        with self.assertRaises(ValueError):
            DocumentationCheck(name="", passed=True, detail="missing name")
        check = DocumentationCheck(name="one", passed=True, detail="valid")
        with self.assertRaises(ValueError):
            DocumentationValidationReport(checks=(check, check))


if __name__ == "__main__":
    unittest.main()
