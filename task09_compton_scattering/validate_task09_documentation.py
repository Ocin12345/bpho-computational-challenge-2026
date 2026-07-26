"""Command-line documentation validation entry point for Task 9."""

from __future__ import annotations

from task09_compton_scattering.documentation_validation import (
    validate_task09_documentation,
)


def main() -> int:
    report = validate_task09_documentation()
    passed = sum(check.passed for check in report.checks)
    print(f"Task 9 documentation validation: {passed}/{len(report.checks)} checks passed")
    for check in report.failed_checks:
        print(f"FAIL {check.name}: {check.detail}")
    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
