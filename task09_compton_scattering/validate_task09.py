"""Command-line validation entry point for Task 9."""

from __future__ import annotations

from task09_compton_scattering.analysis import build_task09_study
from task09_compton_scattering.validation import validate_task09


def main() -> int:
    study = build_task09_study()
    report = validate_task09(study)
    passed_count = sum(check.passed for check in report.checks)
    print(f"Task 9 validation: {passed_count}/{len(report.checks)} checks passed")
    for check in report.failed_checks:
        print(
            f"FAIL {check.name}: observed={check.observed:.12g}, "
            f"expected={check.expected:.12g}, tolerance={check.tolerance:.12g}"
        )
    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
