"""Command-line validation for the implemented portions of Task 3."""

from __future__ import annotations

import argparse
from collections.abc import Sequence

from task03_thermal_radiation.analysis import build_planck_study
from task03_thermal_radiation.validation import validate_planck_study


def main(argv: Sequence[str] | None = None) -> int:
    """Run Stage 5 Planck validation and return a shell exit status."""

    parser = argparse.ArgumentParser(
        description="Validate the implemented Task 3 models.",
    )
    parser.parse_args(argv)

    result = build_planck_study()
    report = validate_planck_study(result)

    print("Task 3 Stage 5: Planck validation")
    for check in report.checks:
        status = "PASS" if check.passed else "FAIL"
        print(
            f"[{status}] {check.name}: observed={check.observed:.12g}, "
            f"expected={check.expected:.12g}, unit={check.unit}, "
            f"comparison={check.comparison}, "
            f"tolerance={check.tolerance:.3g}"
        )
    print(f"Planck validation: {'PASS' if report.passed else 'FAIL'}")
    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
