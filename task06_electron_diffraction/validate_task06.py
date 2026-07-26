"""Command-line validation runner for Task 6."""

from __future__ import annotations

from task06_electron_diffraction.analysis import build_task06_study
from task06_electron_diffraction.validation import validate_task06


def main() -> int:
    study = build_task06_study()
    report = validate_task06(study)
    for check in report.checks:
        status = "PASS" if check.passed else "FAIL"
        print(f"[{status}] {check.name}: {check.explanation}")
    print(
        f"Task 6 validation: {sum(check.passed for check in report.checks)}/"
        f"{len(report.checks)} checks passed"
    )
    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
