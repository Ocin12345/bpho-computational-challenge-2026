"""Tests for state morphing, hybridization and approximate many-electron density."""

from __future__ import annotations

import unittest

import numpy as np
from scipy.integrate import trapezoid

from task10_hydrogenic_orbitals.constants import CONSTANTS
from task10_hydrogenic_orbitals.molecular_hybrid_extension import (
    electron_count,
    h2plus_lcao_wavefunction_scaled,
    h2plus_overlap,
    hybrid_coefficients,
    independent_electron_density_m_neg_three,
    m_state_morph,
    superposition_wavefunction_scaled,
)


class MolecularHybridExtensionTests(unittest.TestCase):
    def test_hybrid_coefficient_sets_are_orthonormal(self) -> None:
        for kind, expected_count in (("sp", 2), ("sp2", 3), ("sp3", 4)):
            _, coefficients = hybrid_coefficients(kind)
            gram = coefficients @ coefficients.conjugate().T
            np.testing.assert_allclose(gram, np.eye(expected_count), atol=2.0e-15)

    def test_m_morph_has_normalized_endpoints_and_midpoints(self) -> None:
        for progress in (0.0, 0.125, 0.5, 0.875, 1.0):
            states, coefficients = m_state_morph(2, progress)
            self.assertEqual(len(states), 5)
            self.assertAlmostEqual(float(np.sum(np.abs(coefficients) ** 2)), 1.0, places=14)
        _, first = m_state_morph(2, 0.0)
        _, last = m_state_morph(2, 1.0)
        self.assertEqual(int(np.argmax(abs(first))), 0)
        self.assertEqual(int(np.argmax(abs(last))), 4)

    def test_superposition_endpoints_equal_basis_states(self) -> None:
        states, coefficients = m_state_morph(1, 0.0)
        coordinates = np.linspace(-2.0, 2.0, 31)
        observed = superposition_wavefunction_scaled(
            states, coefficients, coordinates, 0.3, -0.2
        )
        expected = superposition_wavefunction_scaled(
            (states[0],), [1.0], coordinates, 0.3, -0.2
        )
        np.testing.assert_allclose(observed, expected, atol=0.0, rtol=0.0)

    def test_h2plus_overlap_and_lcao_normalization_identity(self) -> None:
        separation = 2.0
        overlap = h2plus_overlap(separation)
        self.assertGreater(overlap, 0.0)
        self.assertLess(overlap, 1.0)
        bonding_norm = (2.0 + 2.0 * overlap) / (2.0 * (1.0 + overlap))
        antibonding_norm = (2.0 - 2.0 * overlap) / (2.0 * (1.0 - overlap))
        self.assertAlmostEqual(bonding_norm, 1.0, places=15)
        self.assertAlmostEqual(antibonding_norm, 1.0, places=15)
        bonding_at_origin = float(h2plus_lcao_wavefunction_scaled(0.0, 0.0, 0.0, separation))
        antibonding_at_origin = float(
            h2plus_lcao_wavefunction_scaled(0.0, 0.0, 0.0, separation, bonding=False)
        )
        self.assertGreater(bonding_at_origin, 0.0)
        self.assertAlmostEqual(antibonding_at_origin, 0.0, places=15)

    def test_screened_densities_integrate_to_electron_count(self) -> None:
        radius = np.linspace(0.0, 60.0 * CONSTANTS.bohr_radius_m, 120_001)
        for element in ("He", "Li", "C", "Ne"):
            density = independent_electron_density_m_neg_three(element, radius)
            integrated = trapezoid(4.0 * np.pi * radius**2 * density, radius)
            self.assertAlmostEqual(float(integrated), electron_count(element), places=6)
            self.assertTrue(np.all(density >= 0.0))

    def test_antibonding_zero_separation_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            h2plus_lcao_wavefunction_scaled(0.0, 0.0, 0.0, 0.0, bonding=False)


if __name__ == "__main__":
    unittest.main()
