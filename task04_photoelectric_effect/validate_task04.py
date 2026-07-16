"""Validation-only command-line entry point for Task 4."""

from __future__ import annotations

import sys
from collections.abc import Sequence

from task04_photoelectric_effect.analysis import build_task04_study
from task04_photoelectric_effect.validation import validate_task04


def main(argv: Sequence[str] | None = None) -> int:
    """Build, validate, print all checks, and return a shell exit status."""

    arguments = tuple(sys.argv[1:] if argv is None else argv)
    if arguments:
        raise ValueError("the Task 4 validation command accepts no arguments")

    report = validate_task04(build_task04_study())
    for check in report.checks:
        status = "PASS" if check.passed else "FAIL"
        print(
            f"{status:4}  {check.name:34} "
            f"observed={check.observed:.17g} "
            f"expected={check.expected:.17g} "
            f"tolerance={check.tolerance:.17g} "
            f"unit={check.unit} comparison={check.comparison}"
        )
    outcome = "PASS" if report.passed else "FAIL"
    print(
        f"Task 4 validation: {outcome} "
        f"({len(report.checks) - len(report.failed_checks)}/"
        f"{len(report.checks)} checks passed)"
    )
    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
