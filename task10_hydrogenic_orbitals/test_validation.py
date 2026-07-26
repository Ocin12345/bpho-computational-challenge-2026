"""Tests for the Task 10 independent scientific acceptance suite."""

from __future__ import annotations

import unittest

import numpy as np

from task10_hydrogenic_orbitals.models import (
    real_spherical_harmonic,
    scaled_radial_wavefunction,
)
from task10_hydrogenic_orbitals.validation import (
    task10_state_digest,
    validate_task10,
)


class ScientificValidationTests(unittest.TestCase):
    def test_complete_validation_passes(self) -> None:
        report = validate_task10()
        self.assertTrue(
            report.passed,
            msg="; ".join(
                f"{check.name}: {check.maximum_error} > {check.tolerance}"
                for check in report.failed_checks
            ),
        )
        self.assertEqual(len(report.checks), 22)
        self.assertEqual(len(report.state_digest), 64)

    def test_corrupted_radial_normalization_is_detected(self) -> None:
        def corrupted_radial(state, radius):
            return np.asarray(scaled_radial_wavefunction(state, radius)) * 1.001

        report = validate_task10(radial_evaluator=corrupted_radial)
        failed = {check.name for check in report.failed_checks}
        self.assertIn("radial_reference", failed)
        self.assertIn("radial_normalization", failed)
        self.assertIn("mean_radius", failed)

    def test_corrupted_angular_normalization_is_detected(self) -> None:
        def corrupted_angular(l, m, polar, azimuth):
            return (
                np.asarray(real_spherical_harmonic(l, m, polar, azimuth))
                * 0.999
            )

        report = validate_task10(angular_evaluator=corrupted_angular)
        failed = {check.name for check in report.failed_checks}
        self.assertIn("angular_reference", failed)
        self.assertIn("angular_normalization_and_orthogonality", failed)

    def test_state_digest_is_deterministic_and_sensitive(self) -> None:
        first = task10_state_digest()
        second = task10_state_digest()
        self.assertEqual(first, second)
        self.assertNotEqual(first, "0" * 64)


if __name__ == "__main__":
    unittest.main()
