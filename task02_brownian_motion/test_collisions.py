"""Tests for Task 2 small-large contact and restitution physics."""

from __future__ import annotations

import unittest

import numpy as np

from task02_brownian_motion.brownian_motion import (
    BrownianParameters,
    SimulationState,
    resolve_small_large_collisions,
)


def collision_parameters(**overrides: object) -> BrownianParameters:
    """Return transparent masses and geometry for collision tests."""

    values: dict[str, object] = {
        "n_small": 1,
        "small_mass_kg": 1.0,
        "large_mass_kg": 3.0,
        "small_radius_nm": 0.5,
        "large_radius_nm": 1.0,
        "box_size_nm": 10.0,
        "max_time_ps": 0.1,
        "restitution": 1.0,
        "seed": 2026,
    }
    values.update(overrides)
    return BrownianParameters(**values)  # type: ignore[arg-type]


def collision_state(
    small_positions: list[list[float]],
    small_velocities: list[list[float]],
    *,
    large_position: tuple[float, float] = (5.0, 5.0),
    large_velocity: tuple[float, float] = (0.0, 0.0),
) -> SimulationState:
    """Construct a state for isolated collision tests."""

    n_small = len(small_positions)
    return SimulationState(
        small_positions_nm=np.asarray(
            small_positions,
            dtype=np.float64,
        ),
        small_velocities_nm_per_ps=np.asarray(
            small_velocities,
            dtype=np.float64,
        ),
        next_randomization_times_ps=np.ones(n_small, dtype=np.float64),
        large_position_nm=np.asarray(large_position, dtype=np.float64),
        large_velocity_nm_per_ps=np.asarray(
            large_velocity,
            dtype=np.float64,
        ),
    )


def pair_momentum(
    state: SimulationState,
    parameters: BrownianParameters,
) -> np.ndarray:
    """Return total momentum for every small particle plus the tracer."""

    return (
        parameters.small_mass_kg
        * np.sum(state.small_velocities_nm_per_ps, axis=0)
        + parameters.large_mass_kg * state.large_velocity_nm_per_ps
    )


def pair_energy(
    state: SimulationState,
    parameters: BrownianParameters,
) -> float:
    """Return total kinetic energy in the model's velocity units."""

    return 0.5 * (
        parameters.small_mass_kg
        * float(np.sum(state.small_velocities_nm_per_ps**2))
        + parameters.large_mass_kg
        * float(np.dot(
            state.large_velocity_nm_per_ps,
            state.large_velocity_nm_per_ps,
        ))
    )


class ContactSelectionTests(unittest.TestCase):
    """Verify which pairs are processed and which receive an impulse."""

    def test_noncontact_state_is_unchanged(self) -> None:
        parameters = collision_parameters()
        state = collision_state([[2.0, 5.0]], [[1.0, 0.0]])
        before = state.copy()

        report = resolve_small_large_collisions(state, parameters)

        self.assertEqual(report.contacts_detected, 0)
        self.assertEqual(report.impulses_applied, 0)
        self.assertEqual(report.events, ())
        np.testing.assert_array_equal(
            state.small_positions_nm,
            before.small_positions_nm,
        )
        np.testing.assert_array_equal(
            state.small_velocities_nm_per_ps,
            before.small_velocities_nm_per_ps,
        )
        np.testing.assert_array_equal(
            state.large_position_nm,
            before.large_position_nm,
        )
        np.testing.assert_array_equal(
            state.large_velocity_nm_per_ps,
            before.large_velocity_nm_per_ps,
        )

    def test_small_small_overlap_is_deliberately_ignored(self) -> None:
        parameters = collision_parameters(n_small=2)
        state = collision_state(
            [[2.0, 2.0], [2.1, 2.0]],
            [[1.0, 0.0], [-1.0, 0.0]],
        )

        report = resolve_small_large_collisions(state, parameters)

        self.assertEqual(report.contacts_detected, 0)

    def test_separating_overlap_is_corrected_without_an_impulse(self) -> None:
        parameters = collision_parameters()
        state = collision_state([[4.0, 5.0]], [[-1.0, 0.0]])
        velocities_before = (
            state.small_velocities_nm_per_ps.copy(),
            state.large_velocity_nm_per_ps.copy(),
        )

        report = resolve_small_large_collisions(state, parameters)

        self.assertEqual(report.contacts_detected, 1)
        self.assertEqual(report.impulses_applied, 0)
        self.assertEqual(report.separating_contacts, 1)
        event = report.events[0]
        self.assertFalse(event.impulse_applied)
        self.assertGreaterEqual(
            event.relative_normal_speed_before_nm_per_ps,
            0.0,
        )
        self.assertEqual(event.impulse_magnitude_kg_nm_per_ps, 0.0)
        np.testing.assert_array_equal(
            state.small_velocities_nm_per_ps,
            velocities_before[0],
        )
        np.testing.assert_array_equal(
            state.large_velocity_nm_per_ps,
            velocities_before[1],
        )

    def test_clearance_prevents_immediate_redetection(self) -> None:
        parameters = collision_parameters()
        state = collision_state([[4.0, 5.0]], [[-1.0, 0.0]])

        first = resolve_small_large_collisions(state, parameters)
        second = resolve_small_large_collisions(state, parameters)

        self.assertEqual(first.contacts_detected, 1)
        self.assertEqual(second.contacts_detected, 0)


class CollisionImpulseTests(unittest.TestCase):
    """Verify analytical head-on, oblique, elastic, and inelastic results."""

    def test_elastic_head_on_collision_matches_closed_form(self) -> None:
        parameters = collision_parameters()
        state = collision_state([[3.5, 5.0]], [[1.0, 0.0]])

        report = resolve_small_large_collisions(state, parameters)

        np.testing.assert_allclose(
            state.small_velocities_nm_per_ps[0],
            [-0.5, 0.0],
            rtol=0.0,
            atol=2.0e-15,
        )
        np.testing.assert_allclose(
            state.large_velocity_nm_per_ps,
            [0.5, 0.0],
            rtol=0.0,
            atol=2.0e-15,
        )
        event = report.events[0]
        self.assertTrue(event.impulse_applied)
        self.assertAlmostEqual(
            event.relative_normal_speed_before_nm_per_ps,
            -1.0,
        )
        self.assertAlmostEqual(
            event.relative_normal_speed_after_nm_per_ps,
            1.0,
        )
        self.assertAlmostEqual(
            event.impulse_magnitude_kg_nm_per_ps,
            1.5,
        )
        self.assertLess(event.normalized_momentum_error, 1.0e-15)
        self.assertLess(event.normalized_restitution_error, 1.0e-15)
        self.assertLess(event.normalized_energy_identity_error, 1.0e-15)

    def test_oblique_collision_preserves_relative_tangential_speed(
        self,
    ) -> None:
        parameters = collision_parameters(restitution=0.7)
        normal = np.array([0.6, 0.8])
        tangent = np.array([-0.8, 0.6])
        small_position = np.array([5.0, 5.0]) - 1.49 * normal
        small_velocity = 1.2 * normal + 0.7 * tangent
        large_velocity = -0.2 * normal - 0.1 * tangent
        state = collision_state(
            [small_position.tolist()],
            [small_velocity.tolist()],
            large_velocity=tuple(large_velocity),
        )
        momentum_before = pair_momentum(state, parameters)

        report = resolve_small_large_collisions(state, parameters)

        event = report.events[0]
        self.assertAlmostEqual(
            event.relative_normal_speed_after_nm_per_ps,
            -parameters.restitution
            * event.relative_normal_speed_before_nm_per_ps,
            places=14,
        )
        self.assertLess(
            abs(event.relative_tangential_speed_change_nm_per_ps),
            1.0e-14,
        )
        np.testing.assert_allclose(
            pair_momentum(state, parameters),
            momentum_before,
            rtol=0.0,
            atol=2.0e-15,
        )

    def test_inelastic_energy_loss_matches_reduced_mass_identity(self) -> None:
        parameters = collision_parameters(restitution=0.5)
        state = collision_state([[3.5, 5.0]], [[1.0, 0.0]])
        energy_before = pair_energy(state, parameters)

        report = resolve_small_large_collisions(state, parameters)

        event = report.events[0]
        energy_change_j = (
            pair_energy(state, parameters) - energy_before
        ) * 1.0e6
        reduced_mass = (
            parameters.small_mass_kg
            * parameters.large_mass_kg
            / (parameters.small_mass_kg + parameters.large_mass_kg)
        )
        expected_j = (
            -0.5
            * reduced_mass
            * (1.0 - parameters.restitution**2)
            * event.relative_normal_speed_before_nm_per_ps**2
            * 1.0e6
        )
        self.assertAlmostEqual(energy_change_j, expected_j)
        self.assertAlmostEqual(
            event.kinetic_energy_change_j,
            expected_j,
        )
        self.assertAlmostEqual(
            event.expected_kinetic_energy_change_j,
            expected_j,
        )
        self.assertLess(event.normalized_energy_identity_error, 1.0e-15)

    def test_zero_restitution_removes_relative_normal_separation(
        self,
    ) -> None:
        parameters = collision_parameters(restitution=0.0)
        state = collision_state([[3.5, 5.0]], [[1.0, 0.0]])

        report = resolve_small_large_collisions(state, parameters)

        self.assertAlmostEqual(
            report.events[0].relative_normal_speed_after_nm_per_ps,
            0.0,
            places=15,
        )


class OverlapCorrectionTests(unittest.TestCase):
    """Verify weighted correction, residual tolerance, and failure safety."""

    def test_correction_preserves_pair_centre_of_mass(self) -> None:
        parameters = collision_parameters()
        state = collision_state([[4.0, 5.0]], [[-1.0, 0.0]])
        small_before = state.small_positions_nm[0].copy()
        large_before = state.large_position_nm.copy()
        centre_of_mass_before = (
            parameters.small_mass_kg * small_before
            + parameters.large_mass_kg * large_before
        ) / (parameters.small_mass_kg + parameters.large_mass_kg)

        report = resolve_small_large_collisions(state, parameters)

        small_shift = np.linalg.norm(
            state.small_positions_nm[0] - small_before
        )
        large_shift = np.linalg.norm(
            state.large_position_nm - large_before
        )
        centre_of_mass_after = (
            parameters.small_mass_kg * state.small_positions_nm[0]
            + parameters.large_mass_kg * state.large_position_nm
        ) / (parameters.small_mass_kg + parameters.large_mass_kg)
        np.testing.assert_allclose(
            centre_of_mass_after,
            centre_of_mass_before,
            rtol=0.0,
            atol=2.0e-15,
        )
        self.assertAlmostEqual(
            small_shift / large_shift,
            parameters.large_mass_kg / parameters.small_mass_kg,
            places=12,
        )
        event = report.events[0]
        self.assertAlmostEqual(event.penetration_before_nm, 0.5)
        self.assertEqual(event.residual_penetration_nm, 0.0)
        self.assertGreater(
            event.distance_after_correction_nm,
            parameters.small_radius_nm + parameters.large_radius_nm,
        )

    def test_coincident_centres_fail_without_partial_mutation(self) -> None:
        parameters = collision_parameters(n_small=2)
        state = collision_state(
            [[3.6, 5.0], [5.0, 5.0]],
            [[1.0, 0.0], [0.0, 1.0]],
        )
        before = state.copy()

        with self.assertRaises(RuntimeError):
            resolve_small_large_collisions(state, parameters)

        np.testing.assert_array_equal(
            state.small_positions_nm,
            before.small_positions_nm,
        )
        np.testing.assert_array_equal(
            state.small_velocities_nm_per_ps,
            before.small_velocities_nm_per_ps,
        )
        np.testing.assert_array_equal(
            state.large_position_nm,
            before.large_position_nm,
        )
        np.testing.assert_array_equal(
            state.large_velocity_nm_per_ps,
            before.large_velocity_nm_per_ps,
        )


class BatchAndStressTests(unittest.TestCase):
    """Verify deterministic batches and numerical identities at scale."""

    def test_multiple_contacts_conserve_total_vector_momentum(self) -> None:
        parameters = collision_parameters(n_small=3)
        state = collision_state(
            [[3.6, 5.0], [6.4, 5.0], [5.0, 6.4]],
            [[1.0, 0.0], [-1.0, 0.0], [0.0, -1.0]],
        )
        momentum_before = pair_momentum(state, parameters)

        report = resolve_small_large_collisions(state, parameters)

        self.assertEqual(report.contacts_detected, 3)
        self.assertEqual(
            [event.small_particle_index for event in report.events],
            [0, 1, 2],
        )
        np.testing.assert_allclose(
            pair_momentum(state, parameters),
            momentum_before,
            rtol=0.0,
            atol=3.0e-15,
        )
        self.assertLess(
            report.maximum_normalized_momentum_error,
            1.0e-14,
        )
        self.assertLess(
            report.maximum_residual_penetration_nm,
            1.0e-14,
        )

    def test_random_approaching_collisions_meet_numerical_tolerances(
        self,
    ) -> None:
        parameters = BrownianParameters(
            n_small=1,
            restitution=0.63,
            max_time_ps=0.1,
        )
        contact_distance = (
            parameters.small_radius_nm + parameters.large_radius_nm
        )
        rng = np.random.default_rng(9001)
        maximum_momentum_error = 0.0
        maximum_restitution_error = 0.0
        maximum_energy_error = 0.0

        for _ in range(2_000):
            angle = rng.uniform(0.0, 2.0 * np.pi)
            normal = np.array([np.cos(angle), np.sin(angle)])
            small_position = (
                np.array([5.0, 5.0])
                - (contact_distance - 0.01) * normal
            )
            large_velocity = rng.normal(0.0, 3.0, size=2)
            relative = rng.normal(0.0, 3.0, size=2)
            normal_component = float(np.dot(relative, normal))
            if normal_component >= -0.1:
                relative -= (normal_component + 0.1) * normal
            small_velocity = large_velocity - relative
            state = collision_state(
                [small_position.tolist()],
                [small_velocity.tolist()],
                large_velocity=tuple(large_velocity),
            )

            report = resolve_small_large_collisions(state, parameters)
            event = report.events[0]
            self.assertTrue(event.impulse_applied)
            maximum_momentum_error = max(
                maximum_momentum_error,
                event.normalized_momentum_error,
            )
            maximum_restitution_error = max(
                maximum_restitution_error,
                event.normalized_restitution_error,
            )
            maximum_energy_error = max(
                maximum_energy_error,
                event.normalized_energy_identity_error,
            )

        self.assertLess(maximum_momentum_error, 1.0e-12)
        self.assertLess(maximum_restitution_error, 1.0e-12)
        self.assertLess(maximum_energy_error, 1.0e-12)


if __name__ == "__main__":
    unittest.main()
