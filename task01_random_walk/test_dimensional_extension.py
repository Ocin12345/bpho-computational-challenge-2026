"""Deterministic checks for the Task 1 dimensional extension."""

from __future__ import annotations

import unittest

import numpy as np

from task01_random_walk.dimensional_extension import (
    default_checkpoints,
    run_dimension_study,
    sample_isotropic_steps,
    simulate_dimensional_walk,
    theoretical_normalized_radial_density,
)


class DimensionalWalkTests(unittest.TestCase):
    def test_shapes_and_origins_in_every_dimension(self) -> None:
        for dimension in (1, 2, 3):
            with self.subTest(dimension=dimension):
                result = simulate_dimensional_walk(80, 1.25, dimension, seed=7)
                self.assertEqual(result.displacements.shape, (80, dimension))
                self.assertEqual(result.positions.shape, (81, dimension))
                np.testing.assert_array_equal(result.positions[0], np.zeros(dimension))

    def test_every_step_has_the_requested_length(self) -> None:
        for dimension in (1, 2, 3):
            with self.subTest(dimension=dimension):
                result = simulate_dimensional_walk(2_000, 2.75, dimension, seed=91)
                np.testing.assert_allclose(
                    result.step_lengths,
                    2.75,
                    rtol=2.0e-15,
                    atol=3.0e-14,
                )

    def test_one_dimensional_steps_have_only_two_directions(self) -> None:
        rng = np.random.default_rng(3)
        steps = sample_isotropic_steps(rng, 4_000, 1, 0.5)
        self.assertEqual(set(np.unique(steps[:, 0])), {-0.5, 0.5})
        self.assertLess(abs(float(np.mean(steps[:, 0]))), 0.02)

    def test_three_dimensional_steps_are_isotropic(self) -> None:
        rng = np.random.default_rng(5)
        steps = sample_isotropic_steps(rng, 120_000, 3, 1.0)
        np.testing.assert_allclose(np.mean(steps, axis=0), 0.0, atol=0.006)
        np.testing.assert_allclose(np.var(steps, axis=0), 1.0 / 3.0, atol=0.006)

    def test_invalid_dimensions_are_rejected(self) -> None:
        for dimension in (0, 4, -1, 1.5, True):
            with self.subTest(dimension=dimension):
                with self.assertRaises((TypeError, ValueError)):
                    simulate_dimensional_walk(10, 1.0, dimension, seed=1)  # type: ignore[arg-type]


class DimensionStudyTests(unittest.TestCase):
    def test_default_checkpoints_are_ordered_and_end_at_maximum(self) -> None:
        checkpoints = default_checkpoints(800)
        self.assertEqual(checkpoints, tuple(sorted(set(checkpoints))))
        self.assertEqual(checkpoints[-1], 800)
        self.assertGreaterEqual(len(checkpoints), 6)

    def test_rms_law_and_exponent_in_every_dimension(self) -> None:
        for dimension in (1, 2, 3):
            with self.subTest(dimension=dimension):
                study = run_dimension_study(
                    dimension,
                    n_walks=5_000,
                    max_steps=400,
                    seed=2026 + dimension,
                )
                final = study.scaling[-1]
                theory = final.n_steps * study.step_size**2
                self.assertLess(
                    abs(final.mean_squared_displacement / theory - 1.0),
                    0.045,
                )
                self.assertLess(abs(study.slope - 1.0), 0.035)
                self.assertLess(abs(study.exponent - 0.5), 0.035)

    def test_study_is_reproducible(self) -> None:
        first = run_dimension_study(2, n_walks=400, max_steps=80, seed=41)
        second = run_dimension_study(2, n_walks=400, max_steps=80, seed=41)
        np.testing.assert_array_equal(first.normalized_radii, second.normalized_radii)
        self.assertEqual(first.scaling, second.scaling)

    def test_large_n_endpoint_densities_are_normalized(self) -> None:
        q = np.linspace(0.0, 8.0, 200_001)
        for dimension in (1, 2, 3):
            with self.subTest(dimension=dimension):
                density = theoretical_normalized_radial_density(q, dimension)
                self.assertAlmostEqual(
                    float(np.trapezoid(density, q)), 1.0, places=5
                )


if __name__ == "__main__":
    unittest.main()
