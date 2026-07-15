"""Tests for the integrated Task 2 simulation loop and diagnostics."""

from __future__ import annotations

import io
import unittest
from contextlib import redirect_stdout

import numpy as np

from task02_brownian_motion.brownian_motion import (
    BrownianParameters,
    SimulationDiagnostics,
    advance_simulation_step,
    initialize_simulation,
    run_simulation,
)
from task02_brownian_motion.run_task02 import main


def integration_parameters(**overrides: object) -> BrownianParameters:
    """Return a compact official-scale configuration for full-run tests."""

    values: dict[str, object] = {
        "n_small": 100,
        "max_time_ps": 5.0,
        "seed": 7,
    }
    values.update(overrides)
    return BrownianParameters(**values)  # type: ignore[arg-type]


class SimulationDiagnosticTests(unittest.TestCase):
    """Verify immutable diagnostic ownership and validation."""

    def test_zero_diagnostics_have_read_only_matching_histories(self) -> None:
        diagnostics = SimulationDiagnostics.zeros(7)

        self.assertEqual(diagnostics.n_steps, 7)
        self.assertEqual(diagnostics.total_direction_resets, 0)
        self.assertEqual(diagnostics.total_small_wall_impacts, 0)
        self.assertEqual(diagnostics.total_large_wall_impacts, 0)
        self.assertEqual(diagnostics.total_contacts, 0)
        self.assertEqual(diagnostics.total_impulses, 0)
        for array in (
            diagnostics.direction_resets_per_step,
            diagnostics.small_wall_impacts_per_step,
            diagnostics.large_wall_impacts_per_step,
            diagnostics.contacts_per_step,
            diagnostics.impulses_per_step,
            diagnostics.collision_passes_per_step,
        ):
            self.assertEqual(array.shape, (7,))
            self.assertFalse(array.flags.writeable)

    def test_diagnostics_reject_invalid_counts_and_scalars(self) -> None:
        valid = SimulationDiagnostics.zeros(3)
        values = {
            "direction_resets_per_step": valid.direction_resets_per_step,
            "small_wall_impacts_per_step": valid.small_wall_impacts_per_step,
            "large_wall_impacts_per_step": valid.large_wall_impacts_per_step,
            "contacts_per_step": valid.contacts_per_step,
            "impulses_per_step": valid.impulses_per_step,
            "collision_passes_per_step": valid.collision_passes_per_step,
            "maximum_displacement_nm": 0.0,
            "maximum_residual_penetration_nm": 0.0,
            "maximum_normalized_momentum_error": 0.0,
            "maximum_normalized_restitution_error": 0.0,
            "maximum_normalized_energy_identity_error": 0.0,
            "total_collision_energy_change_j": 0.0,
        }
        with self.assertRaises(TypeError):
            SimulationDiagnostics(
                **{
                    **values,
                    "contacts_per_step": np.zeros(3, dtype=np.float64),
                }
            )
        with self.assertRaises(ValueError):
            SimulationDiagnostics(
                **{
                    **values,
                    "impulses_per_step": np.array([0, -1, 0]),
                }
            )
        with self.assertRaises(ValueError):
            SimulationDiagnostics(
                **{
                    **values,
                    "collision_passes_per_step": np.zeros(
                        2,
                        dtype=np.int64,
                    ),
                }
            )
        with self.assertRaises(ValueError):
            SimulationDiagnostics(
                **{
                    **values,
                    "maximum_displacement_nm": np.nan,
                }
            )


class CompleteStepTests(unittest.TestCase):
    """Verify ordering and rollback for one integrated physics step."""

    def test_transport_then_collision_produces_expected_head_on_result(
        self,
    ) -> None:
        parameters = BrownianParameters(
            n_small=1,
            small_mass_kg=1.0,
            large_mass_kg=3.0,
            small_radius_nm=0.5,
            large_radius_nm=1.0,
            box_size_nm=10.0,
            max_time_ps=0.01,
            requested_time_step_ps=0.01,
        )
        context = initialize_simulation(parameters)
        context.state.small_positions_nm[0] = [3.495, 5.0]
        context.state.small_velocities_nm_per_ps[0] = [1.0, 0.0]
        context.state.next_randomization_times_ps[0] = 1.0

        report = advance_simulation_step(context)

        self.assertEqual(context.state.step_index, 1)
        self.assertEqual(context.state.time_ps, 0.01)
        self.assertEqual(report.collisions.contacts_detected, 1)
        self.assertEqual(report.collisions.impulses_applied, 1)
        self.assertEqual(report.collision_passes, 1)
        self.assertEqual(report.remaining_contacts, 0)
        np.testing.assert_allclose(
            context.state.small_velocities_nm_per_ps[0],
            [-0.5, 0.0],
            rtol=0.0,
            atol=2.0e-15,
        )
        np.testing.assert_allclose(
            context.state.large_velocity_nm_per_ps,
            [0.5, 0.0],
            rtol=0.0,
            atol=2.0e-15,
        )

    def test_failed_complete_step_restores_state_and_random_stream(
        self,
    ) -> None:
        parameters = BrownianParameters(
            n_small=1,
            max_time_ps=0.01,
            requested_time_step_ps=0.01,
            seed=33,
        )
        context = initialize_simulation(parameters)
        expected_rng_context = initialize_simulation(parameters)
        centre = np.full(2, parameters.box_size_nm / 2.0)
        context.state.small_positions_nm[0] = centre
        context.state.small_velocities_nm_per_ps[0] = [0.0, 0.0]
        context.state.large_position_nm[:] = centre
        context.state.large_velocity_nm_per_ps[:] = [0.0, 0.0]
        context.state.next_randomization_times_ps[0] = 1.0
        before = context.state.copy()

        with self.assertRaises(RuntimeError):
            advance_simulation_step(context)

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
        np.testing.assert_array_equal(
            context.state.large_position_nm,
            before.large_position_nm,
        )
        np.testing.assert_array_equal(
            context.state.large_velocity_nm_per_ps,
            before.large_velocity_nm_per_ps,
        )
        self.assertEqual(context.state.time_ps, before.time_ps)
        self.assertEqual(context.state.step_index, before.step_index)
        self.assertEqual(
            context.reset_rng.uniform(),
            expected_rng_context.reset_rng.uniform(),
        )


class CompleteRunTests(unittest.TestCase):
    """Verify recording, reproducibility, diagnostics, and final geometry."""

    def test_compact_run_returns_complete_immutable_evidence(self) -> None:
        parameters = integration_parameters()

        result = run_simulation(parameters, max_frames=12)

        diagnostics = result.diagnostics
        self.assertEqual(result.time_grid.final_time_ps, parameters.max_time_ps)
        self.assertEqual(
            result.large_positions_nm.shape,
            (result.time_grid.n_steps + 1, 2),
        )
        self.assertEqual(
            result.small_position_frames_nm.shape,
            (12, parameters.n_small, 2),
        )
        self.assertEqual(diagnostics.n_steps, result.time_grid.n_steps)
        self.assertGreater(diagnostics.total_contacts, 0)
        self.assertGreater(diagnostics.total_impulses, 0)
        self.assertLessEqual(
            diagnostics.maximum_displacement_nm,
            parameters.max_step_fraction * parameters.small_radius_nm,
        )
        self.assertLess(
            diagnostics.maximum_normalized_momentum_error,
            1.0e-12,
        )
        self.assertLess(
            diagnostics.maximum_normalized_restitution_error,
            1.0e-12,
        )
        self.assertLess(
            diagnostics.maximum_normalized_energy_identity_error,
            1.0e-12,
        )
        self.assertLessEqual(
            diagnostics.maximum_residual_penetration_nm,
            1.0e-9
            * (parameters.small_radius_nm + parameters.large_radius_nm),
        )
        self.assertFalse(result.large_positions_nm.flags.writeable)
        self.assertFalse(result.small_position_frames_nm.flags.writeable)
        self.assertFalse(diagnostics.contacts_per_step.flags.writeable)

        final_small_positions = result.small_position_frames_nm[-1]
        final_large_position = result.large_positions_nm[-1]
        final_distances = np.linalg.norm(
            final_small_positions - final_large_position,
            axis=1,
        )
        self.assertTrue(
            np.all(
                final_distances
                > parameters.small_radius_nm + parameters.large_radius_nm
            )
        )
        self.assertTrue(
            np.all(final_small_positions >= parameters.small_radius_nm)
        )
        self.assertTrue(
            np.all(
                final_small_positions
                <= parameters.box_size_nm - parameters.small_radius_nm
            )
        )

    def test_equal_seeds_reproduce_every_recorded_output(self) -> None:
        parameters = integration_parameters(n_small=40, max_time_ps=2.0)

        first = run_simulation(parameters, max_frames=8)
        second = run_simulation(parameters, max_frames=8)

        np.testing.assert_array_equal(
            first.large_positions_nm,
            second.large_positions_nm,
        )
        np.testing.assert_array_equal(
            first.large_velocities_nm_per_ps,
            second.large_velocities_nm_per_ps,
        )
        np.testing.assert_array_equal(
            first.small_position_frames_nm,
            second.small_position_frames_nm,
        )
        np.testing.assert_array_equal(
            first.diagnostics.contacts_per_step,
            second.diagnostics.contacts_per_step,
        )
        np.testing.assert_array_equal(
            first.diagnostics.direction_resets_per_step,
            second.diagnostics.direction_resets_per_step,
        )


class ReferenceSimulationIntegrationTests(unittest.TestCase):
    """Exercise the complete 1,000-particle, 200 ps baseline."""

    def test_complete_reference_simulation_passes_all_runtime_limits(
        self,
    ) -> None:
        result = run_simulation(max_frames=20)
        parameters = result.parameters
        diagnostics = result.diagnostics

        self.assertEqual(result.time_grid.n_steps, 17_706)
        self.assertEqual(result.time_grid.final_time_ps, 200.0)
        self.assertGreater(diagnostics.total_contacts, 0)
        self.assertGreater(diagnostics.total_impulses, 0)
        self.assertGreater(diagnostics.total_direction_resets, 0)
        self.assertLessEqual(
            int(np.max(diagnostics.collision_passes_per_step)),
            parameters.max_collision_passes,
        )
        self.assertLessEqual(
            diagnostics.maximum_displacement_nm,
            parameters.max_step_fraction * parameters.small_radius_nm,
        )
        self.assertLess(
            diagnostics.maximum_normalized_momentum_error,
            1.0e-12,
        )
        self.assertLess(
            diagnostics.maximum_normalized_restitution_error,
            1.0e-12,
        )
        self.assertLess(
            diagnostics.maximum_normalized_energy_identity_error,
            1.0e-12,
        )
        self.assertLessEqual(
            diagnostics.maximum_residual_penetration_nm,
            1.0e-9
            * (parameters.small_radius_nm + parameters.large_radius_nm),
        )
        self.assertEqual(diagnostics.total_large_wall_impacts, 0)
        self.assertGreater(result.final_displacement_nm, 0.0)


class CommandLineTests(unittest.TestCase):
    """Verify that either computer can run a compact case from the terminal."""

    def test_command_line_runner_reports_a_valid_summary(self) -> None:
        output = io.StringIO()

        with redirect_stdout(output):
            exit_code = main(
                [
                    "--particles",
                    "20",
                    "--time-ps",
                    "0.1",
                    "--seed",
                    "4",
                    "--frames",
                    "4",
                ]
            )

        summary = output.getvalue()
        self.assertEqual(exit_code, 0)
        self.assertIn("simulation complete", summary)
        self.assertIn("small particles: 20", summary)
        self.assertIn("final time: 0.100000 ps", summary)
        self.assertIn("maximum normalized errors", summary)


if __name__ == "__main__":
    unittest.main()
