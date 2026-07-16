"""Command-line validation for both deterministic Task 3 models."""

from __future__ import annotations

import argparse
from collections.abc import Sequence

from task03_thermal_radiation.analysis import (
    build_einstein_study,
    build_planck_study,
)
from task03_thermal_radiation.validation import validate_task03


def main(argv: Sequence[str] | None = None) -> int:
    """Run all Task 3 validation checks and return a shell exit status."""

    parser = argparse.ArgumentParser(
        description="Validate the implemented Task 3 models.",
    )
    parser.parse_args(argv)

    planck_result = build_planck_study()
    einstein_result = build_einstein_study()
    report = validate_task03(planck_result, einstein_result)

    print("Task 3 Stage 7: combined validation")
    for check in report.checks:
        status = "PASS" if check.passed else "FAIL"
        print(
            f"[{status}] {check.name}: observed={check.observed:.12g}, "
            f"expected={check.expected:.12g}, unit={check.unit}, "
            f"comparison={check.comparison}, "
            f"tolerance={check.tolerance:.3g}"
        )
    print(f"Task 3 validation: {'PASS' if report.passed else 'FAIL'}")
    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
