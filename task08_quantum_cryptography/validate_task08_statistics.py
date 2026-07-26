"""Command-line validator for the Task 8 finite-photon extension."""

from __future__ import annotations

from task08_quantum_cryptography.statistical_validation import (
    validate_task08_statistics,
)


def main() -> int:
    report = validate_task08_statistics()
    passed = sum(check.passed for check in report.checks)
    print(f"Task 8 statistical validation: {passed}/{len(report.checks)} checks passed")
    if report.passed:
        return 0
    for check in report.failed_checks:
        print(
            f"FAILED {check.name}: observed={check.observed:.17g}, "
            f"expected={check.expected:.17g}, tolerance={check.tolerance:.3g}"
        )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
