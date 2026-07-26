from __future__ import annotations

import unittest

import numpy as np

from task07_particle_in_box.configuration import DEFAULT_CONFIGURATION
from task07_particle_in_box.constants import REDUCED_PLANCK_CONSTANT_J_S
from task07_particle_in_box.models import (
    energy_ev,
    energy_j,
    probability_density_m_inv,
    spatial_wavefunction_m_neg_half,
    time_dependent_wavefunction_m_neg_half,
    uncertainty_product_over_hbar,
)


class AnalyticalModelTests(unittest.TestCase):
    def setUp(self) -> None:
        self.configuration = DEFAULT_CONFIGURATION

    def test_energy_anchors_and_n_squared_scaling(self) -> None:
        n = np.arange(1, 11, dtype=np.int64)
        energies = energy_ev(
            n,
            self.configuration.particle_mass_kg,
            self.configuration.box_width_m,
        )
        self.assertAlmostEqual(float(energies[0]), 0.3760301621048726, places=14)
        np.testing.assert_allclose(energies / energies[0], np.square(n), rtol=2e-15)
        self.assertAlmostEqual(float(energies[-1]), 37.60301621048726, places=12)

    def test_wavefunction_boundaries_outside_and_density(self) -> None:
        width = self.configuration.box_width_m
        positions = np.asarray([-width, 0.0, width / 2.0, width, 2.0 * width])
        states = np.ones(positions.shape, dtype=np.int64)
        wavefunction = spatial_wavefunction_m_neg_half(positions, states, width)
        self.assertEqual(float(wavefunction[0]), 0.0)
        self.assertEqual(float(wavefunction[1]), 0.0)
        self.assertAlmostEqual(float(wavefunction[2]), np.sqrt(2.0 / width))
        self.assertLess(abs(float(wavefunction[3])) / np.sqrt(2.0 / width), 2e-16)
        self.assertEqual(float(wavefunction[4]), 0.0)
        density = probability_density_m_inv(positions, states, width)
        np.testing.assert_allclose(density, np.square(wavefunction), rtol=0.0, atol=0.0)

    def test_time_factor_does_not_change_stationary_density(self) -> None:
        width = self.configuration.box_width_m
        mass = self.configuration.particle_mass_kg
        n = np.asarray([3], dtype=np.int64)
        period = 2.0 * np.pi * REDUCED_PLANCK_CONSTANT_J_S / float(
            energy_j(n, mass, width)[0]
        )
        positions = np.linspace(0.0, width, 101)[:, None]
        times = np.asarray([0.0, 0.17 * period, 0.63 * period])[None, :]
        quantum_numbers = np.full((1, 3), 3, dtype=np.int64)
        psi = time_dependent_wavefunction_m_neg_half(
            positions,
            times,
            quantum_numbers,
            mass,
            width,
        )
        reference_density = probability_density_m_inv(
            positions,
            np.asarray([[3]], dtype=np.int64),
            width,
        )
        np.testing.assert_allclose(
            np.abs(psi) ** 2,
            np.broadcast_to(reference_density, psi.shape),
            rtol=2e-15,
            atol=1e-5,
        )

    def test_uncertainty_anchor_and_bound(self) -> None:
        products = uncertainty_product_over_hbar(np.arange(1, 11, dtype=np.int64))
        self.assertAlmostEqual(float(products[0]), 0.5678618083866119, places=15)
        self.assertTrue(np.all(products >= 0.5))
        self.assertTrue(np.all(np.diff(products) > 0.0))

    def test_rejects_invalid_inputs(self) -> None:
        with self.assertRaises(ValueError):
            energy_j(np.asarray([0]), 1.0, 1.0)
        with self.assertRaises(TypeError):
            energy_j(np.asarray([1.0]), 1.0, 1.0)
        with self.assertRaises(TypeError):
            energy_j(np.asarray([True]), 1.0, 1.0)
        with self.assertRaises(ValueError):
            spatial_wavefunction_m_neg_half(np.asarray([np.nan]), np.asarray([1]), 1.0)
        with self.assertRaises(ValueError):
            probability_density_m_inv(np.asarray([0.5]), np.asarray([1]), -1.0)


if __name__ == "__main__":
    unittest.main()
