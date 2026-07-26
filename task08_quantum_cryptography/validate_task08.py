"""Command-line validation entry point for Task 8."""

from __future__ import annotations

from task08_quantum_cryptography.analysis import build_task08_study
from task08_quantum_cryptography.validation import validate_task08


def main() -> int:
    study = build_task08_study()
    report = validate_task08(study)
    passed_count = sum(check.passed for check in report.checks)
    print(f"Task 8 validation: {passed_count}/{len(report.checks)} checks passed")
    for check in report.failed_checks:
        print(
            f"FAIL {check.name}: observed={check.observed:.12g}, "
            f"expected={check.expected:.12g}, tolerance={check.tolerance:.12g}"
        )
    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
