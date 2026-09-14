from __future__ import annotations

import unittest
from dataclasses import replace

from task07_particle_in_box.analysis import build_task07_study
from task07_particle_in_box.validation import (
    task07_study_digest,
    validate_task07,
)


class ValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.study = build_task07_study()

    def test_complete_validation_passes(self) -> None:
        report = validate_task07(self.study)
        self.assertTrue(report.passed)
        self.assertEqual(len(report.checks), 50)
        self.assertEqual(report.study_digest, task07_study_digest(self.study))
        self.assertEqual(len({check.name for check in report.checks}), 50)

    def test_corrupted_energy_is_detected(self) -> None:
        energies = self.study.energies_j.copy()
        energies[0] *= 1.01
        corrupted = replace(self.study, energies_j=energies)
        report = validate_task07(corrupted)
        self.assertFalse(report.passed)
        failed = {check.name for check in report.failed_checks}
        self.assertIn("energy_decimal_reference", failed)
        self.assertIn("electronvolt_conversion", failed)

    def test_corrupted_uncertainty_is_detected(self) -> None:
        products = self.study.uncertainty_products_over_hbar.copy()
        products[0] = 0.49
        corrupted = replace(self.study, uncertainty_products_over_hbar=products)
        report = validate_task07(corrupted)
        self.assertFalse(report.passed)
        failed = {check.name for check in report.failed_checks}
        self.assertIn("heisenberg_uncertainty_bound", failed)

    def test_digest_changes_with_scientific_state(self) -> None:
        energies = self.study.energies_ev.copy()
        energies[-1] *= 1.0001
        changed = replace(self.study, energies_ev=energies)
        self.assertNotEqual(task07_study_digest(changed), task07_study_digest(self.study))


if __name__ == "__main__":
    unittest.main()
