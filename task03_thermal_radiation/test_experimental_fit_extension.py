"""Regression tests for the Task 3 copper-data fitting extension."""

from __future__ import annotations

import unittest

import numpy as np

from task03_thermal_radiation.experimental_fit_extension import (
    COPPER_REFERENCE_CP_J_MOL_K,
    COPPER_REFERENCE_TEMPERATURE_K,
    copper_reference_uncertainty_j_mol_k,
    fit_copper_heat_capacity,
    lattice_plus_electronic_cp,
)


class CopperHeatCapacityExtensionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.debye = fit_copper_heat_capacity(model="debye")
        cls.einstein = fit_copper_heat_capacity(model="einstein")

    def test_reference_table_inventory_and_anchors(self) -> None:
        self.assertEqual(COPPER_REFERENCE_TEMPERATURE_K.shape, (35,))
        self.assertEqual(COPPER_REFERENCE_CP_J_MOL_K.shape, (35,))
        self.assertAlmostEqual(COPPER_REFERENCE_CP_J_MOL_K[0], 0.000743)
        self.assertAlmostEqual(COPPER_REFERENCE_CP_J_MOL_K[-1], 24.45)
        self.assertTrue(np.all(np.diff(COPPER_REFERENCE_TEMPERATURE_K) > 0.0))

    def test_uncertainty_policy_tracks_published_ranges(self) -> None:
        uncertainty = copper_reference_uncertainty_j_mol_k()
        index_100 = int(np.flatnonzero(COPPER_REFERENCE_TEMPERATURE_K == 100)[0])
        self.assertAlmostEqual(
            uncertainty[index_100], 0.003 * COPPER_REFERENCE_CP_J_MOL_K[index_100]
        )
        self.assertGreaterEqual(float(np.min(uncertainty)), 2.0e-5)

    def test_debye_fit_is_physical_and_recovers_copper_scale(self) -> None:
        self.assertGreater(self.debye.characteristic_temperature_k, 250.0)
        self.assertLess(self.debye.characteristic_temperature_k, 450.0)
        self.assertGreaterEqual(self.debye.electronic_gamma_j_mol_k2, 0.0)
        self.assertGreaterEqual(self.debye.dilation_coefficient_mol_per_j, 0.0)
        self.assertLess(self.debye.rms_error_j_mol_k, 0.45)

    def test_debye_resolves_low_temperature_data_better_than_einstein(self) -> None:
        low = COPPER_REFERENCE_TEMPERATURE_K <= 50.0
        debye_low = float(np.sqrt(np.mean(self.debye.residuals_j_mol_k[low] ** 2)))
        einstein_low = float(
            np.sqrt(np.mean(self.einstein.residuals_j_mol_k[low] ** 2))
        )
        self.assertLess(debye_low, 0.50 * einstein_low)

    def test_model_has_correct_zero_temperature_limit(self) -> None:
        capacity = lattice_plus_electronic_cp(
            np.asarray([0.0]), 340.0, 7.0e-4, 1.0e-6, model="debye"
        )
        self.assertEqual(float(capacity[0]), 0.0)

    def test_invalid_model_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            fit_copper_heat_capacity(model="invented")


if __name__ == "__main__":
    unittest.main()
