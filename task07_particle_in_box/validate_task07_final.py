"""Command-line final acceptance validation entry point for Task 7."""

from __future__ import annotations

from task07_particle_in_box.final_validation import validate_task07_final


def main() -> int:
    report = validate_task07_final()
    passed = sum(check.passed for check in report.checks)
    print(f"Task 7 final artifact validation: {passed}/{len(report.checks)} groups passed")
    for check in report.failed_checks:
        print(f"FAIL {check.name}: {check.detail}")
    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
