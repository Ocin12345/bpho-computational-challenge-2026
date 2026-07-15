"""Command-line runner for Task 2 ensemble experiments and statistics."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from task02_brownian_motion.analysis import (
    ExperimentDesign,
    build_experiment_cases,
    run_statistical_analysis,
    write_analysis_outputs,
)


def build_parser() -> argparse.ArgumentParser:
    """Create the Step 8 analysis command-line parser."""

    parser = argparse.ArgumentParser(
        description=(
            "Run the pre-declared Task 2 ensembles, parameter experiments, "
            "confidence intervals, and MSD analysis."
        )
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=4,
        help="parallel simulation workers (default: 4)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("task02_brownian_motion/analysis"),
        help="directory for JSON and CSV results",
    )
    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=Path("task02_brownian_motion/.analysis_cache"),
        help="local resumable path cache; this directory is not committed",
    )
    return parser


def main(arguments: Sequence[str] | None = None) -> int:
    """Run every unique case, save results, and print acceptance checks."""

    options = build_parser().parse_args(arguments)
    design = ExperimentDesign()
    total_cases = len(build_experiment_cases(design))
    print(
        f"Running {total_cases} unique Task 2 simulations "
        f"with {options.workers} workers"
    )

    def show_progress(completed: int, total: int, label: str) -> None:
        if completed == total or completed % 8 == 0:
            print(f"completed {completed}/{total}: {label}", flush=True)

    report, records, experiment_summaries = run_statistical_analysis(
        design,
        workers=options.workers,
        progress_callback=show_progress,
        cache_directory=options.cache_dir,
    )
    paths = write_analysis_outputs(
        report,
        records,
        experiment_summaries,
        options.output_dir,
    )

    print(f"overall result: {'PASS' if report.passed else 'FAIL'}")
    for check in report.checks:
        status = "PASS" if check.passed else "FAIL"
        print(f"[{status}] {check.name}: {check.measured}")
    print("saved evidence:")
    for path in paths:
        print(f"- {path}")
    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
