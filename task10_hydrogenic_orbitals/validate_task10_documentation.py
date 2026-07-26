"""Command-line Task 10 documentation acceptance report."""

from __future__ import annotations

from task10_hydrogenic_orbitals.documentation_validation import (
    validate_task10_documentation,
)


def main() -> int:
    report = validate_task10_documentation()
    passed = sum(check.passed for check in report.checks)
    print(f"Task 10 documentation validation: {passed}/{len(report.checks)} checks passed")
    for check in report.failed_checks:
        print(f"FAIL {check.name}: {check.detail}")
    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
