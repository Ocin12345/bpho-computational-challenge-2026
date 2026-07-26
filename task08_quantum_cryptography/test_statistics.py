"""Tests for the reproducible finite-photon statistical extension."""

from __future__ import annotations

import math
import unittest

from task08_quantum_cryptography.constants import UINT32_MAXIMUM
from task08_quantum_cryptography.statistics import (
    advance_seed,
    binomial_mismatch_count,
    derived_stream_seed,
    mulberry32_uint32_sequence,
    mulberry32_uniform_sequence,
    simulate_finite_photon_experiment,
    wilson_interval,
)


class StatisticsTests(unittest.TestCase):
    def test_mulberry32_has_frozen_unsigned_outputs(self) -> None:
        self.assertEqual(
            mulberry32_uint32_sequence(0, 5),
            (1144304738, 1416247, 958946056, 627933444, 2007157716),
        )
        uniforms = mulberry32_uniform_sequence(0, 100)
        self.assertEqual(len(uniforms), 100)
        self.assertTrue(all(0.0 <= value < 1.0 for value in uniforms))
        self.assertEqual(uniforms, mulberry32_uniform_sequence(0, 100))

    def test_streams_and_seed_progression_are_distinct_and_reproducible(self) -> None:
        classical = derived_stream_seed(2026, "classical")
        quantum = derived_stream_seed(2026, "quantum")
        self.assertNotEqual(classical, quantum)
        self.assertEqual(classical, 608136546)
        self.assertEqual(quantum, 3084998280)
        self.assertEqual(advance_seed(2026), 2027)
        self.assertEqual(advance_seed(UINT32_MAXIMUM), 0)

    def test_binomial_edges_and_bounds_are_exact(self) -> None:
        self.assertEqual(binomial_mismatch_count(100, 0.0, 5), 0)
        self.assertEqual(binomial_mismatch_count(100, 1.0, 5), 100)
        sample = binomial_mismatch_count(10_000, 0.375, 5)
        self.assertGreaterEqual(sample, 0)
        self.assertLessEqual(sample, 10_000)
        with self.assertRaises(ValueError):
            binomial_mismatch_count(100, -0.1, 5)
        with self.assertRaises(ValueError):
            binomial_mismatch_count(0, 0.5, 5)

    def test_wilson_interval_is_bounded_and_handles_edges(self) -> None:
        zero = wilson_interval(0, 10)
        full = wilson_interval(10, 10)
        self.assertEqual(zero.lower, 0.0)
        self.assertAlmostEqual(zero.upper, 0.2775327998628892)
        self.assertAlmostEqual(full.lower, 0.7224672001371107)
        self.assertLessEqual(full.upper, 1.0)
        middle = wilson_interval(363, 1000)
        self.assertLessEqual(middle.lower, 0.363)
        self.assertGreaterEqual(middle.upper, 0.363)
        with self.assertRaises(ValueError):
            wilson_interval(11, 10)

    def test_official_experiment_has_frozen_cross_language_reference(self) -> None:
        experiment = simulate_finite_photon_experiment(-30, 30, 1000, 2026)
        self.assertEqual(experiment.classical.mismatches, 363)
        self.assertEqual(experiment.quantum.mismatches, 770)
        self.assertAlmostEqual(experiment.classical.theoretical_probability, 3 / 8)
        self.assertAlmostEqual(experiment.quantum.theoretical_probability, 3 / 4)
        self.assertAlmostEqual(experiment.classical.expected_mismatches, 375.0)
        self.assertAlmostEqual(
            experiment.classical.standard_deviation_count,
            math.sqrt(1000 * (3 / 8) * (5 / 8)),
        )
        self.assertAlmostEqual(
            experiment.classical.standardized_residual or 0.0,
            (363 - 375) / math.sqrt(1000 * (3 / 8) * (5 / 8)),
        )
        for sample in (experiment.classical, experiment.quantum):
            self.assertEqual(sample.mismatches + sample.matches, 1000)
            self.assertEqual(sample.observed_probability, sample.mismatches / 1000)
            self.assertLessEqual(sample.wilson_interval.lower, sample.observed_probability)
            self.assertGreaterEqual(sample.wilson_interval.upper, sample.observed_probability)

    def test_degenerate_and_seeded_experiments_are_well_defined(self) -> None:
        aligned = simulate_finite_photon_experiment(0, 0, 100, 7)
        self.assertEqual(aligned.classical.mismatches, 0)
        self.assertEqual(aligned.quantum.mismatches, 0)
        self.assertIsNone(aligned.classical.standardized_residual)
        perpendicular = simulate_finite_photon_experiment(0, 90, 100, 7)
        self.assertEqual(perpendicular.classical.mismatches, 100)
        self.assertEqual(perpendicular.quantum.mismatches, 100)
        self.assertIsNone(perpendicular.quantum.standardized_residual)
        self.assertEqual(
            simulate_finite_photon_experiment(-30, 30, 1000, 2026),
            simulate_finite_photon_experiment(-30, 30, 1000, 2026),
        )
        self.assertNotEqual(
            simulate_finite_photon_experiment(-30, 30, 1000, 2026),
            simulate_finite_photon_experiment(-30, 30, 1000, 2027),
        )

    def test_invalid_experiment_inputs_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            simulate_finite_photon_experiment(-30, 30, 9, 2026)
        with self.assertRaises(ValueError):
            simulate_finite_photon_experiment(-30, 30, 100_001, 2026)
        with self.assertRaises(ValueError):
            simulate_finite_photon_experiment(-30, 30, 1000, 2**32)
        with self.assertRaises(TypeError):
            simulate_finite_photon_experiment(True, 30, 1000, 2026)


if __name__ == "__main__":
    unittest.main()
