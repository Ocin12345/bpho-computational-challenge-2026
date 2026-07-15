"""Tests for Task 2 parameters, initialization, and architecture contracts."""

from __future__ import annotations

import unittest
from dataclasses import FrozenInstanceError

import numpy as np

from task02_brownian_motion.brownian_motion import (
    BrownianParameters,
    BrownianSimulationResult,
    FixedTimeGrid,
    SimulationState,
    build_frame_steps,
    create_time_grid,
    initialize_simulation,
    validate_initial_state,
)


def compact_parameters(**overrides: object) -> BrownianParameters:
    """Return a small, fast parameter set for architecture tests."""

    values: dict[str, object] = {
        "n_small": 12,
        "max_time_ps": 0.25,
        "seed": 2026,
    }
    values.update(overrides)
    return BrownianParameters(**values)  # type: ignore[arg-type]


class BrownianParameterTests(unittest.TestCase):
    """Verify physical defaults, derived quantities, and validation."""

    def test_reference_defaults_match_the_official_example(self) -> None:
        parameters = BrownianParameters()

        self.assertEqual(parameters.n_small, 1_000)
        self.assertAlmostEqual(parameters.small_radius_nm, 0.16)
        self.assertAlmostEqual(parameters.large_radius_nm, 1.60)
        self.assertAlmostEqual(parameters.box_size_nm, 11.20)
        self.assertAlmostEqual(parameters.gas_temperature_k, 373.0)
        self.assertAlmostEqual(
            parameters.large_mass_kg / parameters.small_mass_kg,
            10.0,
        )
        self.assertAlmostEqual(
            parameters.small_speed_nm_per_ps,
            0.566569972,
            places=9,
        )
        self.assertAlmostEqual(
            parameters.randomization_interval_ps,
            4.236016942,
            places=9,
        )
        self.assertAlmostEqual(
            parameters.maximum_time_step_ps,
            0.028240113,
            places=9,
        )

    def test_parameters_are_immutable(self) -> None:
        parameters = BrownianParameters()

        with self.assertRaises(FrozenInstanceError):
            parameters.n_small = 2  # type: ignore[misc]

    def test_invalid_particle_counts_and_seeds_are_rejected(self) -> None:
        for value in (0, -1, 1.5, True):
            with self.subTest(n_small=value):
                with self.assertRaises((TypeError, ValueError)):
                    BrownianParameters(n_small=value)  # type: ignore[arg-type]
        for value in (-1, 1.5, True):
            with self.subTest(seed=value):
                with self.assertRaises((TypeError, ValueError)):
                    BrownianParameters(seed=value)  # type: ignore[arg-type]

    def test_invalid_positive_real_parameters_are_rejected(self) -> None:
        names = (
            "small_mass_kg",
            "large_mass_kg",
            "small_radius_nm",
            "large_radius_nm",
            "box_size_nm",
            "gas_temperature_k",
            "boltzmann_j_per_k",
            "knudsen_parameter",
            "max_time_ps",
        )
        for name in names:
            for value in (0.0, -1.0, np.inf, np.nan, True, "1"):
                with self.subTest(name=name, value=value):
                    with self.assertRaises((TypeError, ValueError)):
                        BrownianParameters(**{name: value})

    def test_restitution_and_fraction_ranges_are_enforced(self) -> None:
        for value in (-0.1, 1.1, np.nan, True):
            with self.subTest(restitution=value):
                with self.assertRaises((TypeError, ValueError)):
                    BrownianParameters(restitution=value)  # type: ignore[arg-type]
        self.assertEqual(BrownianParameters(restitution=0).restitution, 0.0)
        self.assertEqual(BrownianParameters(restitution=1).restitution, 1.0)

        for name in ("max_step_fraction", "randomization_step_fraction"):
            for value in (0.0, -0.1, 1.1, np.inf):
                with self.subTest(name=name, value=value):
                    with self.assertRaises(ValueError):
                        BrownianParameters(**{name: value})

    def test_box_must_leave_space_around_the_large_particle(self) -> None:
        with self.assertRaises(ValueError):
            BrownianParameters(box_size_nm=3.0)

    def test_requested_time_step_must_respect_initial_stability_limit(self) -> None:
        default = BrownianParameters()
        accepted = BrownianParameters(
            requested_time_step_ps=default.maximum_time_step_ps
        )
        self.assertAlmostEqual(
            accepted.requested_time_step_ps,
            default.maximum_time_step_ps,
        )
        with self.assertRaises(ValueError):
            BrownianParameters(
                requested_time_step_ps=1.01 * default.maximum_time_step_ps
            )


class TimeGridTests(unittest.TestCase):
    """Verify exact final time, fixed spacing, and frame scheduling."""

    def test_default_grid_is_fixed_and_reaches_200_ps_exactly(self) -> None:
        parameters = BrownianParameters()
        grid = create_time_grid(parameters)

        self.assertEqual(grid.n_steps, 7_083)
        self.assertEqual(grid.times_ps.shape, (7_084,))
        self.assertEqual(grid.times_ps[0], 0.0)
        self.assertEqual(grid.final_time_ps, parameters.max_time_ps)
        self.assertLessEqual(
            grid.step_size_ps,
            parameters.maximum_time_step_ps,
        )
        np.testing.assert_allclose(
            np.diff(grid.times_ps),
            grid.step_size_ps,
            rtol=2.0e-12,
            atol=5.0e-14,
        )
        self.assertFalse(grid.times_ps.flags.writeable)

    def test_smaller_requested_step_increases_resolution(self) -> None:
        default = compact_parameters()
        refined = compact_parameters(
            requested_time_step_ps=default.maximum_time_step_ps / 2.0
        )

        self.assertGreater(
            create_time_grid(refined).n_steps,
            create_time_grid(default).n_steps,
        )

    def test_invalid_time_grid_spacing_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            FixedTimeGrid(
                step_size_ps=0.1,
                n_steps=3,
                times_ps=np.array([0.0, 0.1, 0.25, 0.3]),
            )

    def test_frame_schedule_contains_endpoints_and_is_compact(self) -> None:
        steps = build_frame_steps(7_083, max_frames=240)

        self.assertEqual(steps[0], 0)
        self.assertEqual(steps[-1], 7_083)
        self.assertLessEqual(len(steps), 240)
        self.assertTrue(np.all(np.diff(steps) > 0))
        self.assertFalse(steps.flags.writeable)

    def test_invalid_frame_schedule_inputs_are_rejected(self) -> None:
        for n_steps, max_frames in ((0, 10), (10, 1), (10, True)):
            with self.subTest(n_steps=n_steps, max_frames=max_frames):
                with self.assertRaises((TypeError, ValueError)):
                    build_frame_steps(n_steps, max_frames=max_frames)


class InitializationTests(unittest.TestCase):
    """Verify deterministic streams, geometry, velocity, and state ownership."""

    def test_default_initialization_has_required_shapes_and_conditions(self) -> None:
        context = initialize_simulation()
        state = context.state
        parameters = context.parameters

        self.assertEqual(state.small_positions_nm.shape, (1_000, 2))
        self.assertEqual(state.small_velocities_nm_per_ps.shape, (1_000, 2))
        self.assertEqual(state.next_randomization_times_ps.shape, (1_000,))
        np.testing.assert_array_equal(
            state.large_position_nm,
            np.array([5.6, 5.6]),
        )
        np.testing.assert_array_equal(
            state.large_velocity_nm_per_ps,
            np.zeros(2),
        )
        self.assertEqual(state.time_ps, 0.0)
        self.assertEqual(state.step_index, 0)
        self.assertTrue(
            np.all(state.small_positions_nm >= parameters.small_radius_nm)
        )
        self.assertTrue(
            np.all(
                state.small_positions_nm
                <= parameters.box_size_nm - parameters.small_radius_nm
            )
        )

    def test_initial_state_passes_deterministic_validation(self) -> None:
        context = initialize_simulation()
        report = validate_initial_state(context.state, context.parameters)

        self.assertTrue(report.passed, report.failures)
        self.assertEqual(report.failures, ())
        self.assertGreaterEqual(report.minimum_small_large_clearance_nm, 0.0)
        self.assertLess(
            report.maximum_small_speed_error_nm_per_ps,
            1.0e-14,
        )

    def test_initial_speeds_and_reset_phases_match_the_specification(self) -> None:
        context = initialize_simulation()
        state = context.state
        parameters = context.parameters

        np.testing.assert_allclose(
            state.small_speeds_nm_per_ps,
            parameters.small_speed_nm_per_ps,
            rtol=2.0e-15,
            atol=2.0e-15,
        )
        self.assertTrue(np.all(state.next_randomization_times_ps >= 0.0))
        self.assertTrue(
            np.all(
                state.next_randomization_times_ps
                < parameters.randomization_interval_ps
            )
        )

    def test_same_seed_reproduces_state_and_future_reset_stream(self) -> None:
        first = initialize_simulation(compact_parameters(seed=71))
        second = initialize_simulation(compact_parameters(seed=71))

        np.testing.assert_array_equal(
            first.state.small_positions_nm,
            second.state.small_positions_nm,
        )
        np.testing.assert_array_equal(
            first.state.small_velocities_nm_per_ps,
            second.state.small_velocities_nm_per_ps,
        )
        np.testing.assert_array_equal(
            first.state.next_randomization_times_ps,
            second.state.next_randomization_times_ps,
        )
        np.testing.assert_array_equal(
            first.reset_rng.uniform(size=20),
            second.reset_rng.uniform(size=20),
        )

    def test_different_seeds_change_the_initial_state(self) -> None:
        first = initialize_simulation(compact_parameters(seed=1))
        second = initialize_simulation(compact_parameters(seed=2))

        self.assertFalse(
            np.array_equal(
                first.state.small_positions_nm,
                second.state.small_positions_nm,
            )
        )
        self.assertFalse(
            np.array_equal(
                first.state.small_velocities_nm_per_ps,
                second.state.small_velocities_nm_per_ps,
            )
        )

    def test_state_copy_owns_independent_arrays(self) -> None:
        original = initialize_simulation(compact_parameters()).state
        copied = original.copy()
        copied.small_positions_nm[0, 0] += 1.0
        copied.large_velocity_nm_per_ps[0] = 2.0

        self.assertNotEqual(
            copied.small_positions_nm[0, 0],
            original.small_positions_nm[0, 0],
        )
        self.assertEqual(original.large_velocity_nm_per_ps[0], 0.0)

    def test_state_rejects_inconsistent_array_shapes(self) -> None:
        with self.assertRaises(ValueError):
            SimulationState(
                small_positions_nm=np.zeros((4, 2)),
                small_velocities_nm_per_ps=np.zeros((3, 2)),
                next_randomization_times_ps=np.zeros(4),
                large_position_nm=np.zeros(2),
                large_velocity_nm_per_ps=np.zeros(2),
            )

    def test_state_rejects_an_empty_particle_collection(self) -> None:
        with self.assertRaises(ValueError):
            SimulationState(
                small_positions_nm=np.zeros((0, 2)),
                small_velocities_nm_per_ps=np.zeros((0, 2)),
                next_randomization_times_ps=np.zeros(0),
                large_position_nm=np.zeros(2),
                large_velocity_nm_per_ps=np.zeros(2),
            )

    def test_validation_reports_mutated_initial_contracts(self) -> None:
        context = initialize_simulation(compact_parameters())
        state = context.state.copy()
        state.large_velocity_nm_per_ps[0] = 1.0
        state.small_positions_nm[0] = state.large_position_nm
        state.small_velocities_nm_per_ps[1] = 0.0
        state.next_randomization_times_ps[2] = (
            context.parameters.randomization_interval_ps
        )

        report = validate_initial_state(state, context.parameters)

        self.assertFalse(report.passed)
        joined = "; ".join(report.failures)
        self.assertIn("exactly at rest", joined)
        self.assertIn("must not overlap", joined)
        self.assertIn("reference speed", joined)
        self.assertIn("reset times", joined)


class ResultContractTests(unittest.TestCase):
    """Verify memory-aware result dimensions and immutable ownership."""

    def make_result(self) -> BrownianSimulationResult:
        parameters = compact_parameters(n_small=8, max_time_ps=0.15)
        grid = create_time_grid(parameters)
        frame_steps = build_frame_steps(grid.n_steps, max_frames=6)
        centre = parameters.box_size_nm / 2.0
        large_positions = np.full(
            (grid.n_steps + 1, 2),
            centre,
            dtype=np.float64,
        )
        large_positions[-1] += np.array([0.3, 0.4])
        large_velocities = np.zeros_like(large_positions)
        small_frames = np.zeros(
            (len(frame_steps), parameters.n_small, 2),
            dtype=np.float64,
        )
        return BrownianSimulationResult(
            parameters=parameters,
            time_grid=grid,
            large_positions_nm=large_positions,
            large_velocities_nm_per_ps=large_velocities,
            frame_steps=frame_steps,
            small_position_frames_nm=small_frames,
        )

    def test_result_properties_and_shapes(self) -> None:
        result = self.make_result()

        np.testing.assert_allclose(
            result.final_position_nm,
            (5.9, 6.0),
            rtol=0.0,
            atol=1.0e-14,
        )
        self.assertAlmostEqual(result.final_displacement_nm, 0.5)
        self.assertEqual(result.n_recorded_frames, len(result.frame_steps))
        self.assertEqual(
            result.small_position_frames_nm.shape,
            (
                result.n_recorded_frames,
                result.parameters.n_small,
                2,
            ),
        )

    def test_result_arrays_are_read_only(self) -> None:
        result = self.make_result()

        for array in (
            result.large_positions_nm,
            result.large_velocities_nm_per_ps,
            result.frame_steps,
            result.small_position_frames_nm,
        ):
            self.assertFalse(array.flags.writeable)
        with self.assertRaises(ValueError):
            result.large_positions_nm[0, 0] = 1.0

    def test_invalid_result_shape_is_rejected(self) -> None:
        valid = self.make_result()
        with self.assertRaises(ValueError):
            BrownianSimulationResult(
                parameters=valid.parameters,
                time_grid=valid.time_grid,
                large_positions_nm=np.zeros((2, 2)),
                large_velocities_nm_per_ps=valid.large_velocities_nm_per_ps,
                frame_steps=valid.frame_steps,
                small_position_frames_nm=valid.small_position_frames_nm,
            )

    def test_nonfinite_result_is_rejected(self) -> None:
        valid = self.make_result()
        positions = valid.large_positions_nm.copy()
        positions[-1, 0] = np.nan

        with self.assertRaises(ValueError):
            BrownianSimulationResult(
                parameters=valid.parameters,
                time_grid=valid.time_grid,
                large_positions_nm=positions,
                large_velocities_nm_per_ps=valid.large_velocities_nm_per_ps,
                frame_steps=valid.frame_steps,
                small_position_frames_nm=valid.small_position_frames_nm,
            )

    def test_result_rejects_a_grid_for_different_parameters(self) -> None:
        valid = self.make_result()
        mismatched_parameters = compact_parameters(
            n_small=valid.parameters.n_small,
            max_time_ps=2.0 * valid.parameters.max_time_ps,
        )

        with self.assertRaises(ValueError):
            BrownianSimulationResult(
                parameters=mismatched_parameters,
                time_grid=valid.time_grid,
                large_positions_nm=valid.large_positions_nm,
                large_velocities_nm_per_ps=valid.large_velocities_nm_per_ps,
                frame_steps=valid.frame_steps,
                small_position_frames_nm=valid.small_position_frames_nm,
            )


if __name__ == "__main__":
    unittest.main()
