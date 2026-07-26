"""Tests for the structured Task 8 statistical validation report."""

from __future__ import annotations

import unittest

from task08_quantum_cryptography.statistical_validation import (
    STATISTICAL_VALIDATION_SCHEMA_VERSION,
    StatisticalValidationCheck,
    StatisticalValidationReport,
    validate_task08_statistics,
)


class StatisticalValidationTests(unittest.TestCase):
    def test_complete_report_passes_with_unique_frozen_checks(self) -> None:
        report = validate_task08_statistics()
        self.assertEqual(report.schema_version, STATISTICAL_VALIDATION_SCHEMA_VERSION)
        self.assertTrue(report.passed)
        self.assertEqual(len(report.checks), 24)
        self.assertEqual(len({check.name for check in report.checks}), 24)
        self.assertEqual(report.failed_checks, ())
        self.assertIn(
            "official_classical_seeded_count",
            {check.name for check in report.checks},
        )
        self.assertIn(
            "large_reference_sample_within_five_sigma",
            {check.name for check in report.checks},
        )

    def test_report_rejects_duplicate_names(self) -> None:
        check = StatisticalValidationCheck(
            name="duplicate",
            passed=True,
            observed=0,
            expected=0,
            tolerance=0,
            comparison="exact_equal",
            explanation="test check",
        )
        with self.assertRaises(ValueError):
            StatisticalValidationReport(
                schema_version=STATISTICAL_VALIDATION_SCHEMA_VERSION,
                checks=(check, check),
            )

    def test_invalid_configuration_type_is_rejected(self) -> None:
        with self.assertRaises(TypeError):
            validate_task08_statistics(object())  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
