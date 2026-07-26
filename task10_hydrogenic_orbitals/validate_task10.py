"""Command-line scientific validation entry point for Task 10."""

from __future__ import annotations

from task10_hydrogenic_orbitals.validation import validate_task10


def main() -> int:
    report = validate_task10()
    passed = sum(check.passed for check in report.checks)
    print(f"Task 10 validation: {passed}/{len(report.checks)} checks passed")
    for check in report.failed_checks:
        print(
            f"FAIL {check.name}: error={check.maximum_error:.6g}, "
            f"tolerance={check.tolerance:.6g}; {check.detail}"
        )
    print(f"State digest: {report.state_digest}")
    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
