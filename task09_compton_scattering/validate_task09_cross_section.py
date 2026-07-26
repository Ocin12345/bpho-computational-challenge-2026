"""Command-line validator for the Task 9 Klein–Nishina extension."""

from __future__ import annotations

import numpy as np

from task09_compton_scattering.configuration import DEFAULT_CONFIGURATION
from task09_compton_scattering.cross_section import build_klein_nishina_study
from task09_compton_scattering.cross_section_validation import (
    validate_cross_section_study,
)
from task09_compton_scattering.models import angle_samples


def main() -> int:
    study = build_klein_nishina_study(
        np.asarray(DEFAULT_CONFIGURATION.incident_energies_kev)[:, None],
        angle_samples()[None, :],
    )
    report = validate_cross_section_study(study)
    passed = sum(check.passed for check in report.checks)
    print(
        f"Task 9 Klein–Nishina validation: {passed}/{len(report.checks)} checks passed"
    )
    for check in report.failed_checks:
        print(
            f"FAIL {check.name}: observed={check.observed:.12g}, "
            f"expected={check.expected:.12g}, tolerance={check.tolerance:.12g}"
        )
    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
