"""Command-line validation entry point for Task 8 documentation."""

from task08_quantum_cryptography.documentation_validation import (
    validate_task08_documentation,
)


def main() -> int:
    report = validate_task08_documentation()
    passed = sum(check.passed for check in report.checks)
    print(f"Task 8 documentation validation: {passed}/{len(report.checks)} checks passed")
    for check in report.checks:
        if not check.passed:
            print(f"FAIL {check.name}: {check.detail}")
    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
