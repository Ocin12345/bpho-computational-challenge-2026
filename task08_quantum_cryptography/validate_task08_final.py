"""Run the complete Task 8 artifact acceptance validator."""

from __future__ import annotations

from task08_quantum_cryptography.final_validation import validate_task08_final


def main() -> int:
    report = validate_task08_final()
    passed = sum(check.passed for check in report.checks)
    print(f"Task 8 final artifact validation: {passed}/{len(report.checks)} groups passed")
    for check in report.failed_checks:
        print(f"FAIL {check.name}: {check.detail}")
    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
