"""Command-line final acceptance validation entry point for Task 9."""

from __future__ import annotations

from task09_compton_scattering.final_validation import validate_task09_final


def main() -> int:
    report = validate_task09_final()
    passed = sum(check.passed for check in report.checks)
    print(f"Task 9 final artifact validation: {passed}/{len(report.checks)} groups passed")
    for check in report.failed_checks:
        print(f"FAIL {check.name}: {check.detail}")
    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
