"""Tests for the Maxwellian all-particle Task 2 extension."""

from __future__ import annotations

import unittest

import numpy as np

from task02_brownian_motion.brownian_motion import BrownianParameters
from task02_brownian_motion.thermal_bath_extension import (
    initialize_maxwellian_hard_disc_state,
    kinetic_temperature_k,
    maxwell_component_scale_nm_per_ps,
    run_maxwellian_hard_disc_simulation,
)


class MaxwellianHardDiscTests(unittest.TestCase):
    def setUp(self) -> None:
        self.parameters = BrownianParameters(
            n_small=64,
            box_size_nm=8.0,
            max_time_ps=1.2,
            max_collision_passes=32,
            seed=2026,
        )

    def test_initial_distribution_has_zero_flow_and_exact_temperature(self) -> None:
        state = initialize_maxwellian_hard_disc_state(self.parameters)
        np.testing.assert_allclose(
            np.mean(state.small_velocities_nm_per_ps, axis=0),
            np.zeros(2),
            atol=1.0e-15,
        )
        inferred = kinetic_temperature_k(
            state.small_velocities_nm_per_ps,
            particle_mass_kg=self.parameters.small_mass_kg,
            boltzmann_j_per_k=self.parameters.boltzmann_j_per_k,
        )
        self.assertAlmostEqual(inferred, self.parameters.gas_temperature_k, places=11)

    def test_component_scale_matches_equipartition(self) -> None:
        scale = maxwell_component_scale_nm_per_ps(self.parameters)
        expected = (
            self.parameters.boltzmann_j_per_k
            * self.parameters.gas_temperature_k
            / self.parameters.small_mass_kg
        ) ** 0.5 / 1000.0
        self.assertAlmostEqual(scale, expected, places=14)

    def test_complete_run_has_all_collision_classes_and_conserves_energy(self) -> None:
        result = run_maxwellian_hard_disc_simulation(self.parameters)
        self.assertEqual(result.direction_resets, 0)
        self.assertGreater(result.gas_gas_impulses, 0)
        self.assertGreater(result.gas_tracer_contacts, 0)
        self.assertLess(abs(result.relative_kinetic_energy_drift), 2.0e-12)
        self.assertLess(
            abs(result.initial_temperature_k / result.target_temperature_k - 1.0),
            1.0e-12,
        )

    def test_seed_reproducibility(self) -> None:
        first = run_maxwellian_hard_disc_simulation(self.parameters)
        second = run_maxwellian_hard_disc_simulation(self.parameters)
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
