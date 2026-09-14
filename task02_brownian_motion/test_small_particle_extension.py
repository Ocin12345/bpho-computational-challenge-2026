"""Tests for the explicit small-particle hard-disc extension."""

from __future__ import annotations

import unittest

import numpy as np

from task02_brownian_motion.brownian_motion import BrownianParameters
from task02_brownian_motion.small_particle_extension import (
    initialize_hard_disc_state,
    resolve_small_small_collisions,
    run_hard_disc_simulation,
)


class SmallSmallCollisionTests(unittest.TestCase):
    def test_head_on_equal_masses_exchange_normal_velocities(self) -> None:
        positions = np.array([[0.0, 0.0], [1.9, 0.0]])
        velocities = np.array([[1.0, 0.0], [0.0, 0.0]])
        report = resolve_small_small_collisions(
            positions,
            velocities,
            radius_nm=1.0,
            mass_kg=2.0,
        )
        np.testing.assert_allclose(velocities, [[0.0, 0.0], [1.0, 0.0]])
        self.assertEqual(report.contacts_detected, 1)
        self.assertEqual(report.impulses_applied, 1)

    def test_elastic_glancing_collision_conserves_pair_invariants(self) -> None:
        positions = np.array([[0.0, 0.0], [1.8, 0.45]])
        velocities = np.array([[0.8, 0.3], [-0.2, -0.1]])
        momentum_before = np.sum(velocities, axis=0)
        energy_before = float(np.sum(velocities**2))
        report = resolve_small_small_collisions(
            positions,
            velocities,
            radius_nm=1.0,
            mass_kg=1.0,
        )
        np.testing.assert_allclose(np.sum(velocities, axis=0), momentum_before)
        self.assertAlmostEqual(float(np.sum(velocities**2)), energy_before)
        self.assertLess(report.maximum_normalized_momentum_error, 1.0e-12)
        self.assertLess(report.maximum_normalized_energy_error, 1.0e-12)
        self.assertLessEqual(report.maximum_residual_penetration_nm, 1.0e-12)

    def test_separating_contact_is_corrected_without_an_impulse(self) -> None:
        positions = np.array([[0.0, 0.0], [1.9, 0.0]])
        velocities = np.array([[-1.0, 0.0], [1.0, 0.0]])
        before = velocities.copy()
        report = resolve_small_small_collisions(
            positions,
            velocities,
            radius_nm=1.0,
            mass_kg=1.0,
        )
        np.testing.assert_allclose(velocities, before)
        self.assertEqual(report.contacts_detected, 1)
        self.assertEqual(report.impulses_applied, 0)


class HardDiscBathTests(unittest.TestCase):
    def setUp(self) -> None:
        self.parameters = BrownianParameters(
            n_small=48,
            box_size_nm=8.0,
            max_time_ps=1.5,
            seed=2026,
        )

    def test_initial_state_has_no_small_small_or_tracer_overlap(self) -> None:
        state = initialize_hard_disc_state(self.parameters)
        row, column = np.triu_indices(self.parameters.n_small, k=1)
        pair_distances = np.linalg.norm(
            state.small_positions_nm[column] - state.small_positions_nm[row],
            axis=1,
        )
        tracer_distances = np.linalg.norm(
            state.small_positions_nm - state.large_position_nm,
            axis=1,
        )
        self.assertTrue(
            np.all(pair_distances > 2.0 * self.parameters.small_radius_nm)
        )
        self.assertTrue(
            np.all(
                tracer_distances
                > self.parameters.small_radius_nm
                + self.parameters.large_radius_nm
            )
        )

    def test_hard_disc_run_has_collisions_and_no_direction_resets(self) -> None:
        result = run_hard_disc_simulation(self.parameters, max_frames=24)
        self.assertGreater(result.total_small_small_impulses, 0)
        self.assertEqual(result.direction_resets, 0)
        self.assertLess(abs(result.relative_kinetic_energy_drift), 1.0e-12)
        self.assertLess(result.maximum_normalized_momentum_error, 1.0e-12)
        self.assertLess(result.maximum_normalized_energy_error, 1.0e-12)
        self.assertEqual(result.tracer_positions_nm.shape, (24, 2))


if __name__ == "__main__":
    unittest.main()
