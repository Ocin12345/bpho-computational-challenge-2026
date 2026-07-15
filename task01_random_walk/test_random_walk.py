"""Deterministic tests for the Task 1 random-walk simulation."""

from __future__ import annotations

import io
import unittest
from contextlib import redirect_stdout

import numpy as np

from task01_random_walk.random_walk import (
    main,
    simulate_random_walk,
    simulate_random_walk_ensemble,
    validate_ensemble,
    validate_walk,
)


class RandomWalkSimulationTests(unittest.TestCase):
    """Verify the exact requirements that do not rely on ensemble statistics."""

    def test_result_includes_origin_and_all_positions(self) -> None:
        result = simulate_random_walk(25, 1.5, seed=2026)

        self.assertEqual(result.angles.shape, (25,))
        self.assertEqual(result.displacements.shape, (25, 2))
        self.assertEqual(result.positions.shape, (26, 2))
        np.testing.assert_array_equal(result.positions[0], np.array([0.0, 0.0]))

    def test_angles_are_in_required_half_open_interval(self) -> None:
        result = simulate_random_walk(10_000, 1.0, seed=19)

        self.assertTrue(np.all(result.angles >= 0.0))
        self.assertTrue(np.all(result.angles < 2.0 * np.pi))

    def test_every_step_has_requested_length(self) -> None:
        result = simulate_random_walk(10_000, 2.75, seed=7)

        np.testing.assert_allclose(
            result.step_lengths,
            2.75,
            rtol=2.0e-15,
            atol=2.0e-14,
        )

    def test_positions_are_cumulative_displacements(self) -> None:
        result = simulate_random_walk(500, 0.25, seed=44)

        np.testing.assert_allclose(
            np.diff(result.positions, axis=0),
            result.displacements,
            rtol=2.0e-15,
            atol=1.0e-14,
        )

    def test_same_seed_reproduces_exactly_the_same_walk(self) -> None:
        first = simulate_random_walk(100, 1.0, seed=12345)
        second = simulate_random_walk(100, 1.0, seed=12345)

        np.testing.assert_array_equal(first.angles, second.angles)
        np.testing.assert_array_equal(first.positions, second.positions)

    def test_different_seeds_produce_different_walks(self) -> None:
        first = simulate_random_walk(100, 1.0, seed=1)
        second = simulate_random_walk(100, 1.0, seed=2)

        self.assertFalse(np.array_equal(first.angles, second.angles))

    def test_validation_report_passes_for_valid_walk(self) -> None:
        result = simulate_random_walk(1_000, 1.25, seed=91)
        report = validate_walk(result)

        self.assertTrue(report.passed, report.failures)
        self.assertEqual(report.failures, ())
        self.assertLess(report.max_step_length_error, 1.0e-12)

    def test_final_position_and_distance_match_stored_result(self) -> None:
        result = simulate_random_walk(100, 0.5, seed=12)

        self.assertEqual(result.final_position, tuple(result.positions[-1]))
        self.assertAlmostEqual(
            result.final_distance,
            float(np.linalg.norm(result.positions[-1])),
        )

    def test_invalid_step_counts_are_rejected(self) -> None:
        for value in (0, -1, 1.5, True):
            with self.subTest(value=value):
                with self.assertRaises((TypeError, ValueError)):
                    simulate_random_walk(value, 1.0)  # type: ignore[arg-type]

    def test_invalid_step_sizes_are_rejected(self) -> None:
        for value in (0.0, -1.0, np.inf, np.nan, True, "1.0"):
            with self.subTest(value=value):
                with self.assertRaises((TypeError, ValueError)):
                    simulate_random_walk(10, value)  # type: ignore[arg-type]

    def test_invalid_seeds_are_rejected(self) -> None:
        for value in (-1, 1.5, True):
            with self.subTest(value=value):
                with self.assertRaises((TypeError, ValueError)):
                    simulate_random_walk(10, 1.0, seed=value)  # type: ignore[arg-type]

    def test_command_line_entry_point_reports_success(self) -> None:
        output = io.StringIO()

        with redirect_stdout(output):
            exit_code = main(["--steps", "20", "--step-size", "2", "--seed", "8"])

        self.assertEqual(exit_code, 0)
        self.assertIn("stored positions: 21", output.getvalue())
        self.assertIn("validation: PASS", output.getvalue())


class RandomWalkEnsembleTests(unittest.TestCase):
    """Verify deterministic requirements for a collection of walks."""

    def test_ensemble_shapes_and_origins(self) -> None:
        result = simulate_random_walk_ensemble(50, 1_000, 1.0, seed=2026)

        self.assertEqual(result.angles.shape, (50, 1_000))
        self.assertEqual(result.displacements.shape, (50, 1_000, 2))
        self.assertEqual(result.positions.shape, (50, 1_001, 2))
        np.testing.assert_array_equal(
            result.positions[:, 0, :],
            np.zeros((50, 2)),
        )

    def test_every_ensemble_step_has_requested_length(self) -> None:
        result = simulate_random_walk_ensemble(50, 1_000, 1.75, seed=88)

        np.testing.assert_allclose(
            result.step_lengths,
            1.75,
            rtol=2.0e-15,
            atol=2.0e-14,
        )

    def test_ensemble_is_reproducible_from_master_seed(self) -> None:
        first = simulate_random_walk_ensemble(12, 100, 1.0, seed=991)
        second = simulate_random_walk_ensemble(12, 100, 1.0, seed=991)

        np.testing.assert_array_equal(first.angles, second.angles)
        np.testing.assert_array_equal(first.positions, second.positions)

    def test_ensemble_final_properties_have_one_value_per_walk(self) -> None:
        result = simulate_random_walk_ensemble(25, 80, 0.5, seed=43)

        self.assertEqual(result.final_positions.shape, (25, 2))
        self.assertEqual(result.final_distances.shape, (25,))
        np.testing.assert_allclose(
            result.final_distances,
            np.linalg.norm(result.positions[:, -1, :], axis=1),
        )

    def test_valid_ensemble_passes_validation(self) -> None:
        result = simulate_random_walk_ensemble(50, 1_000, 1.0, seed=2026)
        report = validate_ensemble(result)

        self.assertTrue(report.passed, report.failures)
        self.assertEqual(report.failures, ())
        self.assertLess(report.max_step_length_error, 1.0e-12)

    def test_invalid_walk_counts_are_rejected(self) -> None:
        for value in (0, -1, 2.5, True):
            with self.subTest(value=value):
                with self.assertRaises((TypeError, ValueError)):
                    simulate_random_walk_ensemble(  # type: ignore[arg-type]
                        value,
                        100,
                        1.0,
                    )


if __name__ == "__main__":
    unittest.main()
