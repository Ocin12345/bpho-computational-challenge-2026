"""Tests for Task 2 ensemble design, statistics, execution, and output."""

from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np

from task02_brownian_motion.analysis import (
    AnalysisCheck,
    ExperimentDesign,
    RunRecord,
    SimulationCase,
    Task2AnalysisReport,
    build_experiment_cases,
    execute_cases,
    summarize_records,
    write_analysis_outputs,
)
from task02_brownian_motion.brownian_motion import BrownianParameters


def synthetic_brownian_records(
    *,
    count: int = 32,
    diffusion: float = 0.01,
) -> tuple[RunRecord, ...]:
    """Create reproducible two-dimensional Brownian paths for metric tests."""

    rng = np.random.default_rng(808)
    times = np.linspace(0.0, 200.0, 1_001)
    time_step = times[1] - times[0]
    scale = np.sqrt(2.0 * diffusion * time_step)
    records: list[RunRecord] = []
    for index in range(count):
        increments = rng.normal(0.0, scale, size=(len(times) - 1, 2))
        displacement = np.vstack(
            (np.zeros((1, 2)), np.cumsum(increments, axis=0))
        )
        records.append(
            RunRecord(
                configuration_id="baseline",
                factor_name="baseline",
                factor_value=1.0,
                seed=3_000 + index,
                times_ps=times,
                displacement_x_nm=displacement[:, 0],
                displacement_y_nm=displacement[:, 1],
                total_contacts=1_000,
                total_impulses=800,
                total_direction_resets=5_000,
                total_small_wall_impacts=100,
                total_large_wall_impacts=0,
                maximum_collision_passes=3,
                maximum_displacement_nm=0.01,
                maximum_residual_penetration_nm=0.0,
                maximum_normalized_momentum_error=1.0e-15,
                maximum_normalized_restitution_error=1.0e-15,
                maximum_normalized_energy_identity_error=1.0e-15,
            )
        )
    return tuple(records)


class ExperimentDesignTests(unittest.TestCase):
    """Verify the pre-declared design and case de-duplication."""

    def test_default_design_contains_224_unique_cases(self) -> None:
        design = ExperimentDesign()
        cases = build_experiment_cases(design)

        self.assertEqual(len(cases), 224)
        keys = {
            (case.configuration_id, case.seed) for case in cases
        }
        self.assertEqual(len(keys), len(cases))
        self.assertEqual(
            sum(case.configuration_id == "baseline" for case in cases),
            64,
        )
        self.assertEqual(
            sum(
                case.configuration_id == "time_step_half"
                for case in cases
            ),
            64,
        )

    def test_invalid_design_counts_and_windows_are_rejected(self) -> None:
        invalid_overrides = (
            {"baseline_run_count": 3},
            {"comparison_run_count": 65},
            {"time_step_run_count": 65},
            {"fit_start_ps": 100.0, "fit_end_ps": 20.0},
            {"bootstrap_resamples": 99},
        )
        for overrides in invalid_overrides:
            with self.subTest(overrides=overrides):
                with self.assertRaises(ValueError):
                    ExperimentDesign(**overrides)


class EnsembleMetricTests(unittest.TestCase):
    """Verify confidence intervals and diffusion recovery on known data."""

    def test_synthetic_brownian_ensemble_recovers_positive_diffusion(
        self,
    ) -> None:
        records = synthetic_brownian_records()
        design = ExperimentDesign(
            baseline_run_count=32,
            time_step_run_count=16,
            bootstrap_resamples=500,
        )

        summary = summarize_records(
            records,
            summary_id="synthetic",
            factor_name="synthetic",
            factor_value=1.0,
            design=design,
        )

        self.assertGreater(summary.diffusion_ci_low_nm2_per_ps, 0.0)
        self.assertLess(
            abs(summary.diffusion_coefficient_nm2_per_ps - 0.01),
            0.006,
        )
        self.assertGreater(summary.msd_fit_r_squared, 0.8)
        self.assertEqual(summary.run_count, 32)

    def test_mismatched_time_grids_are_rejected(self) -> None:
        records = list(synthetic_brownian_records(count=4))
        first = records[0]
        records[0] = RunRecord(
            **{
                **first.__dict__,
                "times_ps": first.times_ps + 0.01,
            }
        )

        with self.assertRaises(ValueError):
            summarize_records(
                records,
                summary_id="bad",
                factor_name="bad",
                factor_value=0.0,
                design=ExperimentDesign(bootstrap_resamples=100),
            )


class CaseExecutionTests(unittest.TestCase):
    """Verify the spawn-worker payload using a compact sequential case."""

    def test_compact_case_executes_and_records_diagnostics(self) -> None:
        parameters = BrownianParameters(
            n_small=20,
            max_time_ps=0.1,
            seed=4,
        )
        case = SimulationCase(
            configuration_id="compact",
            factor_name="test",
            factor_value=1.0,
            seed=4,
            parameters=parameters,
        )

        records = execute_cases((case,), workers=1)

        self.assertEqual(len(records), 1)
        record = records[0]
        self.assertEqual(record.seed, 4)
        self.assertEqual(record.times_ps[-1], 0.1)
        self.assertEqual(record.displacement_x_nm.shape, record.times_ps.shape)
        self.assertLessEqual(record.maximum_displacement_nm, 0.016)

    def test_completed_case_is_reused_from_parameter_sensitive_cache(
        self,
    ) -> None:
        parameters = BrownianParameters(
            n_small=10,
            max_time_ps=0.1,
            seed=9,
        )
        case = SimulationCase(
            configuration_id="cached",
            factor_name="test",
            factor_value=1.0,
            seed=9,
            parameters=parameters,
        )
        progress_labels: list[str] = []

        with tempfile.TemporaryDirectory() as temporary_directory:
            first = execute_cases(
                (case,),
                workers=1,
                cache_directory=temporary_directory,
            )
            second = execute_cases(
                (case,),
                workers=1,
                cache_directory=temporary_directory,
                progress_callback=(
                    lambda completed, total, label: progress_labels.append(
                        label
                    )
                ),
            )
            self.assertEqual(
                len(list(Path(temporary_directory).glob("*.npz"))),
                1,
            )

        np.testing.assert_array_equal(
            first[0].displacement_x_nm,
            second[0].displacement_x_nm,
        )
        self.assertTrue(any("cached" in label for label in progress_labels))


class AnalysisOutputTests(unittest.TestCase):
    """Verify JSON and every CSV output using synthetic records."""

    def test_analysis_outputs_are_parseable_and_complete(self) -> None:
        records = synthetic_brownian_records()
        design = ExperimentDesign(
            baseline_run_count=32,
            time_step_run_count=16,
            bootstrap_resamples=100,
        )
        summary = summarize_records(
            records,
            summary_id="baseline_32",
            factor_name="baseline",
            factor_value=1.0,
            design=design,
        )
        report = Task2AnalysisReport(
            design=design,
            checks=(
                AnalysisCheck(
                    name="synthetic",
                    passed=True,
                    measured="pass",
                    threshold="pass",
                    explanation="output test",
                ),
            ),
            summaries=(summary,),
            experiment_summary_ids={"synthetic": ("baseline_32",)},
            interpretations=("synthetic interpretation",),
        )

        with tempfile.TemporaryDirectory() as temporary_directory:
            paths = write_analysis_outputs(
                report,
                records,
                {"synthetic": (summary,)},
                Path(temporary_directory),
            )

            self.assertEqual(len(paths), 5)
            self.assertTrue(all(path.is_file() for path in paths))
            with paths[0].open(encoding="utf-8") as handle:
                decoded = json.load(handle)
            self.assertTrue(decoded["passed"])
            with paths[1].open(encoding="utf-8", newline="") as handle:
                summaries = list(csv.DictReader(handle))
            with paths[2].open(encoding="utf-8", newline="") as handle:
                comparisons = list(csv.DictReader(handle))
            with paths[3].open(encoding="utf-8", newline="") as handle:
                time_series = list(csv.DictReader(handle))
            with paths[4].open(encoding="utf-8", newline="") as handle:
                run_metrics = list(csv.DictReader(handle))
            self.assertEqual(len(summaries), 1)
            self.assertEqual(len(comparisons), 1)
            self.assertEqual(len(time_series), 1_001)
            self.assertEqual(len(run_metrics), 32)


if __name__ == "__main__":
    unittest.main()
