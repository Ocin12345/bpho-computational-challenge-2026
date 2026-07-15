"""Tests for Task 2 numerical convergence and validation reporting."""

from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

from task02_brownian_motion.brownian_motion import BrownianParameters
from task02_brownian_motion.validation import (
    Task2ValidationReport,
    ValidationCheck,
    controlled_collision_convergence,
    reference_time_step_refinement,
    write_validation_report,
)


class ControlledConvergenceTests(unittest.TestCase):
    """Verify phase-averaged first-order collision convergence."""

    def test_rms_error_decreases_at_approximately_first_order(self) -> None:
        rows = controlled_collision_convergence(
            step_counts=(8, 16, 32),
            phase_count=9,
        )

        errors = [row.rms_endpoint_error_nm for row in rows]
        self.assertGreater(errors[0], errors[1])
        self.assertGreater(errors[1], errors[2])
        orders = [
            row.observed_order_from_previous
            for row in rows[1:]
        ]
        self.assertTrue(all(order is not None for order in orders))
        self.assertGreater(min(float(order) for order in orders), 0.8)

    def test_invalid_convergence_design_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            controlled_collision_convergence(step_counts=(8, 16))
        with self.assertRaises(ValueError):
            controlled_collision_convergence(
                step_counts=(8, 16, 32),
                phase_count=3,
            )
        with self.assertRaises(ValueError):
            controlled_collision_convergence(
                step_counts=(8, 0, 32),
                phase_count=5,
            )


class ReferenceRefinementTests(unittest.TestCase):
    """Verify aligned complete-run time-step refinements."""

    def test_compact_refinement_grids_align_and_pass_invariants(self) -> None:
        parameters = BrownianParameters(
            n_small=100,
            max_time_ps=5.0,
            seed=7,
        )

        rows, results = reference_time_step_refinement(
            parameters,
            refinement_factors=(1, 2),
            max_frames=6,
        )

        self.assertEqual(len(rows), 2)
        self.assertEqual(len(results), 2)
        self.assertEqual(rows[1].n_steps, 2 * rows[0].n_steps)
        self.assertAlmostEqual(
            rows[1].time_step_ps,
            rows[0].time_step_ps / 2.0,
        )
        for row in rows:
            self.assertLess(
                row.maximum_normalized_momentum_error,
                1.0e-12,
            )
            self.assertLess(
                row.maximum_normalized_restitution_error,
                1.0e-12,
            )
            self.assertLess(
                row.maximum_normalized_energy_identity_error,
                1.0e-12,
            )

    def test_invalid_refinement_factors_are_rejected(self) -> None:
        parameters = BrownianParameters(n_small=2, max_time_ps=0.1)
        for factors in ((2, 4), (1,), (1, 3, 4), (1, 2.5)):
            with self.subTest(factors=factors):
                with self.assertRaises(ValueError):
                    reference_time_step_refinement(
                        parameters,
                        refinement_factors=factors,
                        max_frames=2,
                    )


class ValidationSerializationTests(unittest.TestCase):
    """Verify durable JSON and CSV evidence."""

    def test_report_writes_parseable_evidence_files(self) -> None:
        controlled = controlled_collision_convergence(
            step_counts=(8, 16, 32),
            phase_count=5,
        )
        refinement, _ = reference_time_step_refinement(
            BrownianParameters(
                n_small=10,
                max_time_ps=0.1,
                seed=2,
            ),
            refinement_factors=(1, 2),
            max_frames=2,
        )
        report = Task2ValidationReport(
            model="test model",
            seed=2,
            checks=(
                ValidationCheck(
                    name="test_check",
                    passed=True,
                    measured="1",
                    threshold=">= 1",
                    explanation="serialization test",
                ),
            ),
            controlled_convergence=controlled,
            reference_refinement=refinement,
            interpretation=("test interpretation",),
        )

        with tempfile.TemporaryDirectory() as temporary_directory:
            paths = write_validation_report(
                report,
                Path(temporary_directory),
            )

            self.assertTrue(all(path.is_file() for path in paths))
            with paths[0].open(encoding="utf-8") as handle:
                decoded = json.load(handle)
            self.assertTrue(decoded["passed"])
            self.assertEqual(decoded["checks"][0]["name"], "test_check")
            with paths[1].open(encoding="utf-8", newline="") as handle:
                controlled_rows = list(csv.DictReader(handle))
            with paths[2].open(encoding="utf-8", newline="") as handle:
                refinement_rows = list(csv.DictReader(handle))
            self.assertEqual(len(controlled_rows), 3)
            self.assertEqual(len(refinement_rows), 2)


if __name__ == "__main__":
    unittest.main()
