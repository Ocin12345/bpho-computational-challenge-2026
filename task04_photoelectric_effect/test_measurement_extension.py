"""Tests for the inverse photoelectric measurement extension."""

from __future__ import annotations

import unittest

import numpy as np

from task04_photoelectric_effect.constants import PLANCK_CONSTANT_J_S
from task04_photoelectric_effect.measurement_extension import (
    MILLIKAN_1916_SLOPES_V_S,
    fit_photoelectric_measurements,
    millikan_1916_planck_estimate,
    run_recovery_study,
    simulate_photoelectric_measurements,
)


class PhotoelectricMeasurementExtensionTests(unittest.TestCase):
    def test_exact_data_recovers_planck_and_work_function(self) -> None:
        frequency = np.linspace(6.2e14, 1.15e15, 12)
        slope = PLANCK_CONSTANT_J_S / 1.602176634e-19
        voltage = slope * frequency - 2.4
        fit = fit_photoelectric_measurements(
            frequency, voltage, np.full(frequency.shape, 0.02)
        )
        self.assertAlmostEqual(fit.planck_constant_j_s / PLANCK_CONSTANT_J_S, 1.0, places=12)
        self.assertAlmostEqual(fit.work_function_ev, 2.4, places=12)
        self.assertLess(float(np.max(np.abs(fit.residuals_v))), 1.0e-12)

    def test_seeded_synthetic_experiment_is_reproducible(self) -> None:
        frequency = np.linspace(6.2e14, 1.15e15, 12)
        first, sigma_first = simulate_photoelectric_measurements(frequency, seed=77)
        second, sigma_second = simulate_photoelectric_measurements(frequency, seed=77)
        np.testing.assert_array_equal(first, second)
        np.testing.assert_array_equal(sigma_first, sigma_second)

    def test_monte_carlo_recovery_is_unbiased_with_calibrated_intervals(self) -> None:
        study = run_recovery_study(experiment_count=600, seed=91)
        self.assertLess(abs(study.relative_planck_bias), 2.5e-3)
        self.assertLess(abs(study.work_function_bias_ev), 0.005)
        self.assertGreater(study.planck_95_percent_coverage, 0.90)
        self.assertLess(study.planck_95_percent_coverage, 0.99)
        self.assertGreater(study.work_function_95_percent_coverage, 0.90)

    def test_millikan_table_is_preserved_and_close_to_modern_h(self) -> None:
        self.assertEqual(MILLIKAN_1916_SLOPES_V_S.shape, (9,))
        planck, standard_error, relative_difference = millikan_1916_planck_estimate()
        self.assertGreater(standard_error, 0.0)
        self.assertLess(abs(relative_difference), 0.01)
        self.assertGreater(planck, 0.0)

    def test_rank_deficient_measurements_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            fit_photoelectric_measurements([1.0, 1.0, 1.0], [0.0, 0.0, 0.0], [1.0, 1.0, 1.0])


if __name__ == "__main__":
    unittest.main()
