"""Tests for the independent Task 9 scientific validation report."""

from __future__ import annotations

import unittest
from dataclasses import replace

from task09_compton_scattering.analysis import build_task09_study
from task09_compton_scattering.validation import (
    task09_study_digest,
    validate_task09,
)


class ValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.study = build_task09_study()

    def test_complete_validation_passes(self) -> None:
        report = validate_task09(self.study)
        self.assertTrue(report.passed)
        self.assertEqual(len(report.checks), 44)
        self.assertEqual(len({check.name for check in report.checks}), 44)
        self.assertEqual(report.study_digest, task09_study_digest(self.study))

    def test_corrupted_fractional_shift_is_detected(self) -> None:
        values = self.study.fractional_wavelength_shift.copy()
        values[2, 360] += 0.01
        corrupted = replace(self.study, fractional_wavelength_shift=values)
        report = validate_task09(corrupted)
        self.assertFalse(report.passed)
        failed = {check.name for check in report.failed_checks}
        self.assertIn("fractional_shift_identity", failed)
        self.assertIn("fractional_shift_reference", failed)

    def test_corrupted_momentum_is_detected(self) -> None:
        values = self.study.electron_pc_kev.copy()
        values[4, 500] *= 1.02
        corrupted = replace(self.study, electron_pc_kev=values)
        report = validate_task09(corrupted)
        self.assertFalse(report.passed)
        failed = {check.name for check in report.failed_checks}
        self.assertIn("momentum_magnitude_identity", failed)
        self.assertIn("electron_mass_shell", failed)
        self.assertIn("electron_momentum_reference", failed)

    def test_digest_changes_with_any_scientific_state(self) -> None:
        values = self.study.electron_recoil_angle_deg.copy()
        values[0, 1] -= 1.0e-6
        changed = replace(self.study, electron_recoil_angle_deg=values)
        self.assertNotEqual(task09_study_digest(changed), task09_study_digest(self.study))


if __name__ == "__main__":
    unittest.main()
