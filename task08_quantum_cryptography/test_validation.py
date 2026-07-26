from __future__ import annotations

import unittest
from dataclasses import replace

from task08_quantum_cryptography.analysis import build_task08_study
from task08_quantum_cryptography.validation import (
    task08_study_digest,
    validate_task08,
)


class ValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.study = build_task08_study()

    def test_complete_validation_passes(self) -> None:
        report = validate_task08(self.study)
        self.assertTrue(report.passed)
        self.assertEqual(len(report.checks), 42)
        self.assertEqual(report.study_digest, task08_study_digest(self.study))
        self.assertEqual(len({check.name for check in report.checks}), 42)

    def test_corrupted_classical_sweep_is_detected(self) -> None:
        values = self.study.sweep_classical_mismatch.copy()
        values[240] += 0.01
        corrupted = replace(self.study, sweep_classical_mismatch=values)
        report = validate_task08(corrupted)
        self.assertFalse(report.passed)
        failed = {check.name for check in report.failed_checks}
        self.assertIn("sweep_classical_complement", failed)
        self.assertIn("sweep_classical_double_angle_reference", failed)
        self.assertIn("official_classical_anchor", failed)

    def test_corrupted_quantum_grid_is_detected(self) -> None:
        values = self.study.grid_quantum_mismatch.copy()
        values[60, 120] -= 0.02
        corrupted = replace(self.study, grid_quantum_mismatch=values)
        report = validate_task08(corrupted)
        self.assertFalse(report.passed)
        failed = {check.name for check in report.failed_checks}
        self.assertIn("grid_quantum_complement", failed)
        self.assertIn("grid_quantum_double_angle_reference", failed)
        self.assertIn("grid_official_quantum", failed)

    def test_digest_changes_with_scientific_state(self) -> None:
        values = self.study.grid_signed_difference.copy()
        values[0, 0] += 1.0e-6
        changed = replace(self.study, grid_signed_difference=values)
        self.assertNotEqual(task08_study_digest(changed), task08_study_digest(self.study))


if __name__ == "__main__":
    unittest.main()
