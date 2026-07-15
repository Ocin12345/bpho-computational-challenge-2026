"""Tests for Task 2 free motion, direction resets, and reflecting walls."""

from __future__ import annotations

import unittest

import numpy as np

from task02_brownian_motion.brownian_motion import (
    BrownianParameters,
    SimulationState,
    advance_free_motion,
    advance_transport_step,
    initialize_simulation,
    randomize_expired_directions,
    reflect_square_walls,
)


def transport_parameters(**overrides: object) -> BrownianParameters:
    """Return a compact parameter set suitable for transport tests."""

    values: dict[str, object] = {
        "n_small": 4,
        "small_radius_nm": 0.5,
        "large_radius_nm": 1.0,
        "box_size_nm": 10.0,
        "max_time_ps": 0.2,
        "seed": 2026,
    }
    values.update(overrides)
    return BrownianParameters(**values)  # type: ignore[arg-type]


def state_from_rows(
    positions: list[list[float]],
    velocities: list[list[float]],
    *,
    reset_times: list[float] | None = None,
    large_position: tuple[float, float] = (5.0, 5.0),
    large_velocity: tuple[float, float] = (0.0, 0.0),
    time_ps: float = 0.0,
    step_index: int = 0,
) -> SimulationState:
    """Construct a concise state for a unit test."""

    n_small = len(positions)
    if reset_times is None:
        reset_times = [1.0] * n_small
    return SimulationState(
        small_positions_nm=np.asarray(positions, dtype=np.float64),
        small_velocities_nm_per_ps=np.asarray(
            velocities,
            dtype=np.float64,
        ),
        next_randomization_times_ps=np.asarray(
            reset_times,
            dtype=np.float64,
        ),
        large_position_nm=np.asarray(large_position, dtype=np.float64),
        large_velocity_nm_per_ps=np.asarray(
            large_velocity,
            dtype=np.float64,
        ),
        time_ps=time_ps,
        step_index=step_index,
    )


class FreeMotionTests(unittest.TestCase):
    """Verify the constant-velocity position update in isolation."""

    def test_free_motion_updates_every_position_but_not_time(self) -> None:
        state = state_from_rows(
            [[2.0, 3.0], [4.0, 5.0]],
            [[1.0, -2.0], [-0.5, 0.25]],
            large_velocity=(0.1, -0.2),
        )

        maximum_displacement = advance_free_motion(state, 0.4)

        np.testing.assert_allclose(
            state.small_positions_nm,
            [[2.4, 2.2], [3.8, 5.1]],
            rtol=0.0,
            atol=1.0e-15,
        )
        np.testing.assert_allclose(
            state.large_position_nm,
            [5.04, 4.92],
            rtol=0.0,
            atol=1.0e-15,
        )
        self.assertAlmostEqual(
            maximum_displacement,
            np.hypot(1.0, -2.0) * 0.4,
        )
        self.assertEqual(state.time_ps, 0.0)
        self.assertEqual(state.step_index, 0)

    def test_free_motion_rejects_invalid_steps_and_velocities(self) -> None:
        state = state_from_rows([[2.0, 2.0]], [[1.0, 0.0]])
        for value in (0.0, -1.0, np.inf, np.nan, True):
            with self.subTest(time_step=value):
                with self.assertRaises((TypeError, ValueError)):
                    advance_free_motion(state.copy(), value)

        state.small_velocities_nm_per_ps[0, 0] = np.nan
        with self.assertRaises(ValueError):
            advance_free_motion(state, 0.1)


class DirectionResetTests(unittest.TestCase):
    """Verify reset scheduling, speed restoration, and random reproducibility."""

    def test_only_expired_particles_reset_in_index_order(self) -> None:
        parameters = transport_parameters(n_small=3)
        interval = parameters.randomization_interval_ps
        state = state_from_rows(
            [[2.0, 2.0], [3.0, 3.0], [4.0, 4.0]],
            [[0.1, 0.2], [0.3, 0.4], [-0.5, 0.6]],
            reset_times=[0.0, 0.5 * interval, 0.0],
        )
        unchanged_velocity = state.small_velocities_nm_per_ps[1].copy()
        rng = np.random.default_rng(73)
        expected_rng = np.random.default_rng(73)
        expected_angles = expected_rng.uniform(0.0, 2.0 * np.pi, size=2)

        count = randomize_expired_directions(state, parameters, rng)

        self.assertEqual(count, 2)
        expected_velocities = parameters.small_speed_nm_per_ps * np.column_stack(
            (np.cos(expected_angles), np.sin(expected_angles))
        )
        np.testing.assert_allclose(
            state.small_velocities_nm_per_ps[[0, 2]],
            expected_velocities,
            rtol=2.0e-15,
            atol=2.0e-15,
        )
        np.testing.assert_array_equal(
            state.small_velocities_nm_per_ps[1],
            unchanged_velocity,
        )
        np.testing.assert_allclose(
            state.next_randomization_times_ps,
            [interval, 0.5 * interval, interval],
            rtol=2.0e-15,
            atol=2.0e-15,
        )

    def test_reset_restores_the_prescribed_speed(self) -> None:
        parameters = transport_parameters(n_small=2)
        state = state_from_rows(
            [[2.0, 2.0], [3.0, 3.0]],
            [[100.0, -20.0], [0.0, 0.0]],
            reset_times=[0.0, 0.0],
        )

        randomize_expired_directions(
            state,
            parameters,
            np.random.default_rng(11),
        )

        np.testing.assert_allclose(
            state.small_speeds_nm_per_ps,
            parameters.small_speed_nm_per_ps,
            rtol=2.0e-15,
            atol=2.0e-15,
        )

    def test_no_expired_timer_consumes_no_random_number(self) -> None:
        parameters = transport_parameters(n_small=1)
        state = state_from_rows(
            [[2.0, 2.0]],
            [[1.0, 0.0]],
            reset_times=[1.0],
        )
        rng = np.random.default_rng(18)
        expected_rng = np.random.default_rng(18)

        count = randomize_expired_directions(state, parameters, rng)

        self.assertEqual(count, 0)
        self.assertEqual(rng.uniform(), expected_rng.uniform())

    def test_more_than_one_overdue_interval_is_rejected(self) -> None:
        parameters = transport_parameters(n_small=1)
        interval = parameters.randomization_interval_ps
        state = state_from_rows(
            [[2.0, 2.0]],
            [[1.0, 0.0]],
            reset_times=[0.0],
            time_ps=interval,
        )

        with self.assertRaises(RuntimeError):
            randomize_expired_directions(
                state,
                parameters,
                np.random.default_rng(1),
            )


class WallReflectionTests(unittest.TestCase):
    """Verify radius-aware elastic reflection, including edge cases."""

    def test_small_and_large_particles_use_their_own_radii(self) -> None:
        parameters = transport_parameters(n_small=2)
        state = state_from_rows(
            [[9.7, 3.0], [0.3, 7.0]],
            [[1.0, 0.0], [-2.0, 0.0]],
            large_position=(9.2, 5.0),
            large_velocity=(0.5, 0.0),
        )
        small_speeds_before = state.small_speeds_nm_per_ps.copy()
        large_speed_before = np.linalg.norm(state.large_velocity_nm_per_ps)

        report = reflect_square_walls(state, parameters)

        self.assertEqual(report.small_particle_impacts, 2)
        self.assertEqual(report.large_particle_impacts, 1)
        self.assertEqual(report.total_impacts, 3)
        np.testing.assert_allclose(
            state.small_positions_nm,
            [[9.3, 3.0], [0.7, 7.0]],
            rtol=0.0,
            atol=1.0e-15,
        )
        np.testing.assert_allclose(
            state.small_velocities_nm_per_ps,
            [[-1.0, 0.0], [2.0, 0.0]],
        )
        np.testing.assert_allclose(state.large_position_nm, [8.8, 5.0])
        np.testing.assert_allclose(
            state.large_velocity_nm_per_ps,
            [-0.5, 0.0],
        )
        np.testing.assert_allclose(
            state.small_speeds_nm_per_ps,
            small_speeds_before,
        )
        self.assertEqual(
            np.linalg.norm(state.large_velocity_nm_per_ps),
            large_speed_before,
        )

    def test_corner_and_exact_wall_arrivals_flip_required_components(self) -> None:
        parameters = transport_parameters(n_small=2)
        state = state_from_rows(
            [[9.7, 0.3], [9.5, 0.5]],
            [[1.0, -1.0], [2.0, -3.0]],
        )

        report = reflect_square_walls(state, parameters)

        self.assertEqual(report.small_particle_impacts, 4)
        np.testing.assert_allclose(
            state.small_positions_nm,
            [[9.3, 0.7], [9.5, 0.5]],
            rtol=0.0,
            atol=1.0e-15,
        )
        np.testing.assert_allclose(
            state.small_velocities_nm_per_ps,
            [[-1.0, 1.0], [-2.0, 3.0]],
        )

    def test_multiple_crossings_are_folded_without_losing_speed(self) -> None:
        parameters = transport_parameters(n_small=2)
        width = (
            parameters.box_size_nm - 2.0 * parameters.small_radius_nm
        )
        state = state_from_rows(
            [
                [parameters.small_radius_nm + 2.2 * width, 3.0],
                [parameters.small_radius_nm - 1.2 * width, 7.0],
            ],
            [[4.0, 0.0], [-5.0, 0.0]],
        )

        report = reflect_square_walls(state, parameters)

        self.assertEqual(report.small_particle_impacts, 4)
        np.testing.assert_allclose(
            state.small_positions_nm[:, 0],
            [
                parameters.small_radius_nm + 0.2 * width,
                parameters.small_radius_nm + 0.8 * width,
            ],
            rtol=0.0,
            atol=5.0e-15,
        )
        np.testing.assert_allclose(
            state.small_velocities_nm_per_ps[:, 0],
            [4.0, -5.0],
        )

    def test_inconsistent_outside_state_is_rejected(self) -> None:
        parameters = transport_parameters(n_small=1)
        state = state_from_rows([[0.3, 3.0]], [[1.0, 0.0]])

        with self.assertRaises(ValueError):
            reflect_square_walls(state, parameters)


class OrderedTransportStepTests(unittest.TestCase):
    """Verify ordering, safety checks, exact time, and repeated transport."""

    def test_reset_happens_before_motion(self) -> None:
        parameters = transport_parameters(n_small=1, max_time_ps=0.02, seed=8)
        context = initialize_simulation(parameters)
        expected_context = initialize_simulation(parameters)
        context.state.small_positions_nm[0] = [3.0, 3.0]
        context.state.small_velocities_nm_per_ps[0] = [0.0, 0.0]
        context.state.next_randomization_times_ps[0] = 0.0
        expected_angle = expected_context.reset_rng.uniform(0.0, 2.0 * np.pi)
        expected_velocity = parameters.small_speed_nm_per_ps * np.array(
            [np.cos(expected_angle), np.sin(expected_angle)]
        )
        expected_position = (
            np.array([3.0, 3.0])
            + expected_velocity * context.time_grid.step_size_ps
        )

        report = advance_transport_step(context)

        self.assertEqual(report.direction_resets, 1)
        np.testing.assert_allclose(
            context.state.small_velocities_nm_per_ps[0],
            expected_velocity,
            rtol=2.0e-15,
            atol=2.0e-15,
        )
        np.testing.assert_allclose(
            context.state.small_positions_nm[0],
            expected_position,
            rtol=2.0e-15,
            atol=2.0e-15,
        )

    def test_step_commits_exact_grid_time_and_a_complete_report(self) -> None:
        context = initialize_simulation(transport_parameters())

        report = advance_transport_step(context)

        self.assertEqual(context.state.step_index, 1)
        self.assertEqual(
            context.state.time_ps,
            context.time_grid.times_ps[1],
        )
        self.assertEqual(report.step_index, 1)
        self.assertEqual(report.start_time_ps, 0.0)
        self.assertEqual(report.end_time_ps, context.time_grid.times_ps[1])
        self.assertEqual(report.time_step_ps, context.time_grid.step_size_ps)
        self.assertLessEqual(
            report.maximum_displacement_nm,
            report.displacement_limit_nm,
        )
        self.assertLess(
            report.maximum_small_speed_error_nm_per_ps,
            1.0e-14,
        )

    def test_displacement_failure_is_transactional(self) -> None:
        parameters = transport_parameters(n_small=1, max_time_ps=0.02)
        context = initialize_simulation(parameters)
        expected_rng_context = initialize_simulation(parameters)
        context.state.small_velocities_nm_per_ps[0] = [1.0e6, 0.0]
        context.state.next_randomization_times_ps[0] = 0.0
        context.state.large_velocity_nm_per_ps[0] = 1.0e6
        before = context.state.copy()

        with self.assertRaises(RuntimeError):
            advance_transport_step(context)

        np.testing.assert_array_equal(
            context.state.small_positions_nm,
            before.small_positions_nm,
        )
        np.testing.assert_array_equal(
            context.state.small_velocities_nm_per_ps,
            before.small_velocities_nm_per_ps,
        )
        np.testing.assert_array_equal(
            context.state.next_randomization_times_ps,
            before.next_randomization_times_ps,
        )
        self.assertEqual(context.state.time_ps, before.time_ps)
        self.assertEqual(context.state.step_index, before.step_index)
        self.assertEqual(
            context.reset_rng.uniform(),
            expected_rng_context.reset_rng.uniform(),
        )

    def test_due_reset_can_restore_an_unsafe_small_speed_before_motion(
        self,
    ) -> None:
        parameters = transport_parameters(n_small=1, max_time_ps=0.02)
        context = initialize_simulation(parameters)
        context.state.small_velocities_nm_per_ps[0] = [1.0e6, 0.0]
        context.state.next_randomization_times_ps[0] = 0.0

        report = advance_transport_step(context)

        self.assertEqual(report.direction_resets, 1)
        self.assertLessEqual(
            report.maximum_displacement_nm,
            report.displacement_limit_nm,
        )
        self.assertAlmostEqual(
            context.state.small_speeds_nm_per_ps[0],
            parameters.small_speed_nm_per_ps,
        )

    def test_repeated_transport_is_reproducible_and_stays_inside_walls(self) -> None:
        parameters = transport_parameters(
            n_small=64,
            max_time_ps=15.0,
            seed=91,
        )
        first = initialize_simulation(parameters)
        second = initialize_simulation(parameters)
        first_reset_count = 0
        second_reset_count = 0

        while first.state.step_index < first.time_grid.n_steps:
            first_reset_count += advance_transport_step(first).direction_resets
            second_reset_count += advance_transport_step(second).direction_resets

        self.assertEqual(first.state.time_ps, parameters.max_time_ps)
        self.assertEqual(second.state.time_ps, parameters.max_time_ps)
        self.assertGreaterEqual(first_reset_count, parameters.n_small)
        self.assertEqual(first_reset_count, second_reset_count)
        np.testing.assert_array_equal(
            first.state.small_positions_nm,
            second.state.small_positions_nm,
        )
        np.testing.assert_array_equal(
            first.state.small_velocities_nm_per_ps,
            second.state.small_velocities_nm_per_ps,
        )
        self.assertTrue(
            np.all(
                first.state.small_positions_nm
                >= parameters.small_radius_nm
            )
        )
        self.assertTrue(
            np.all(
                first.state.small_positions_nm
                <= parameters.box_size_nm - parameters.small_radius_nm
            )
        )
        np.testing.assert_array_equal(
            first.state.large_position_nm,
            np.full(2, parameters.box_size_nm / 2.0),
        )
        np.testing.assert_array_equal(
            first.state.large_velocity_nm_per_ps,
            np.zeros(2),
        )

    def test_step_rejects_time_mismatch_and_advancing_past_the_end(self) -> None:
        context = initialize_simulation(
            transport_parameters(n_small=1, max_time_ps=0.02)
        )
        context.state.time_ps = 0.001
        with self.assertRaises(RuntimeError):
            advance_transport_step(context)

        context = initialize_simulation(
            transport_parameters(n_small=1, max_time_ps=0.02)
        )
        while context.state.step_index < context.time_grid.n_steps:
            advance_transport_step(context)
        with self.assertRaises(RuntimeError):
            advance_transport_step(context)


class ReferenceTransportIntegrationTests(unittest.TestCase):
    """Exercise every transport step in the official 200 ps reference run."""

    def test_complete_reference_transport_remains_valid(self) -> None:
        context = initialize_simulation()
        total_resets = 0
        total_wall_impacts = 0
        maximum_displacement = 0.0

        while context.state.step_index < context.time_grid.n_steps:
            report = advance_transport_step(context)
            total_resets += report.direction_resets
            total_wall_impacts += report.total_wall_impacts
            maximum_displacement = max(
                maximum_displacement,
                report.maximum_displacement_nm,
            )

        parameters = context.parameters
        state = context.state
        self.assertEqual(state.step_index, context.time_grid.n_steps)
        self.assertEqual(state.time_ps, parameters.max_time_ps)
        self.assertGreater(total_resets, 0)
        self.assertGreater(total_wall_impacts, 0)
        self.assertLessEqual(
            maximum_displacement,
            parameters.max_step_fraction * parameters.small_radius_nm,
        )
        self.assertTrue(np.all(np.isfinite(state.small_positions_nm)))
        self.assertTrue(np.all(np.isfinite(state.small_velocities_nm_per_ps)))
        self.assertTrue(
            np.all(state.small_positions_nm >= parameters.small_radius_nm)
        )
        self.assertTrue(
            np.all(
                state.small_positions_nm
                <= parameters.box_size_nm - parameters.small_radius_nm
            )
        )
        np.testing.assert_array_equal(
            state.large_position_nm,
            np.full(2, parameters.box_size_nm / 2.0),
        )
        np.testing.assert_array_equal(
            state.large_velocity_nm_per_ps,
            np.zeros(2),
        )


if __name__ == "__main__":
    unittest.main()
