"""Validation-only command-line entry point for Task 5."""

from __future__ import annotations

import sys
from collections.abc import Sequence

from task05_hydrogen_spectrum.analysis import build_task05_study
from task05_hydrogen_spectrum.validation import validate_task05


def main(argv: Sequence[str] | None = None) -> int:
    arguments = tuple(sys.argv[1:] if argv is None else argv)
    if arguments:
        raise ValueError("the Task 5 validation command accepts no arguments")

    report = validate_task05(build_task05_study())
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
        f"Task 5 validation: {outcome} "
        f"({len(report.checks) - len(report.failed_checks)}/"
        f"{len(report.checks)} checks passed)"
    )
    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
