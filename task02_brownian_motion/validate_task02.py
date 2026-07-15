"""Command-line entry point for Task 2 numerical validation."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from task02_brownian_motion.validation import (
    run_validation_suite,
    write_validation_report,
)


def build_parser() -> argparse.ArgumentParser:
    """Create the validation command-line parser."""

    parser = argparse.ArgumentParser(
        description=(
            "Run controlled collision convergence and full reference "
            "time-step refinement for BPhO Task 2."
        )
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("task02_brownian_motion/validation"),
        help="directory for JSON and CSV evidence",
    )
    return parser


def main(arguments: Sequence[str] | None = None) -> int:
    """Run, save, and summarize the complete validation suite."""

    options = build_parser().parse_args(arguments)
    report = run_validation_suite()
    paths = write_validation_report(report, options.output_dir)

    print("Task 2 numerical validation complete")
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
