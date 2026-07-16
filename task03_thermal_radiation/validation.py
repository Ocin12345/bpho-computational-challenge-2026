"""Structured validation for the deterministic Task 3 models."""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from task03_thermal_radiation.analysis import PlanckStudyResult
from task03_thermal_radiation.configuration import Task03Configuration


@dataclass(frozen=True)
class ValidationCheck:
    """One stable, serializable scientific validation result."""

    name: str
    passed: bool
    observed: float
    expected: float
    tolerance: float
    comparison: str
    unit: str
    explanation: str

    def __post_init__(self) -> None:
        if not isinstance(self.name, str):
            raise TypeError("validation check name must be a string")
        if not self.name or any(character.isspace() for character in self.name):
            raise ValueError("validation check name must be non-empty and stable")
        if not isinstance(self.passed, bool):
            raise TypeError("passed must be a bool")
        for field_name in ("observed", "expected", "tolerance"):
            value = float(getattr(self, field_name))
            if not math.isfinite(value):
                raise ValueError(f"{field_name} must be finite")
            object.__setattr__(self, field_name, value)
        if self.tolerance < 0.0:
            raise ValueError("tolerance must be non-negative")
        if not isinstance(self.comparison, str):
            raise TypeError("comparison must be a string")
        if not self.comparison:
            raise ValueError("comparison must be non-empty")
        if not isinstance(self.unit, str):
            raise TypeError("unit must be a string")
        if not isinstance(self.explanation, str):
            raise TypeError("explanation must be a string")
        if not self.explanation:
            raise ValueError("explanation must be non-empty")


@dataclass(frozen=True)
class Task03ValidationReport:
    """Immutable collection of all validation checks available so far."""

    schema_version: int
    passed: bool
    checks: tuple[ValidationCheck, ...]

    def __post_init__(self) -> None:
        if isinstance(self.schema_version, bool) or not isinstance(
            self.schema_version, int
        ):
            raise TypeError("schema_version must be an integer")
        if self.schema_version <= 0:
            raise ValueError("schema_version must be positive")
        if not isinstance(self.passed, bool):
            raise TypeError("passed must be a bool")
        checks = tuple(self.checks)
        if not checks:
            raise ValueError("checks must not be empty")
        if not all(isinstance(check, ValidationCheck) for check in checks):
            raise TypeError("checks must contain ValidationCheck records")
        if len({check.name for check in checks}) != len(checks):
            raise ValueError("validation check names must be unique")
        expected_passed = all(check.passed for check in checks)
        if self.passed is not expected_passed:
            raise ValueError("report passed state must match its checks")
        object.__setattr__(self, "checks", checks)

    @property
    def failures(self) -> tuple[ValidationCheck, ...]:
        """Return failed checks in stable report order."""

        return tuple(check for check in self.checks if not check.passed)


def _relative_error(observed: float, expected: float) -> float:
    """Return absolute relative error for a non-zero expected value."""

    if expected == 0.0:
        raise ValueError("relative-error reference must be non-zero")
    return abs(observed - expected) / abs(expected)


def _temperature_label(temperature_k: float) -> str:
    """Return a stable lower-case identifier for one reference temperature."""

    if temperature_k.is_integer():
        return f"{int(temperature_k)}_k"
    return f"{temperature_k:g}_k".replace(".", "p")


def validate_planck_study(
    result: PlanckStudyResult,
    configuration: Task03Configuration | None = None,
) -> Task03ValidationReport:
    """Validate a Planck study against every pre-declared Stage 5 check."""

    if not isinstance(result, PlanckStudyResult):
        raise TypeError("result must be a PlanckStudyResult")
    if configuration is None:
        configuration = result.configuration
    if not isinstance(configuration, Task03Configuration):
        raise TypeError("configuration must be a Task03Configuration")
    if configuration != result.configuration:
        raise ValueError("configuration must match the study result")

    checks: list[ValidationCheck] = []

    spectra_finite = bool(
        np.all(np.isfinite(result.spectral_radiance_w_m3_sr))
        and np.all(np.isfinite(result.spectral_exitance_w_m2_nm))
    )
    checks.append(
        ValidationCheck(
            name="planck_spectra_finite",
            passed=spectra_finite,
            observed=float(spectra_finite),
            expected=1.0,
            tolerance=0.0,
            comparison="exact",
            unit="dimensionless",
            explanation="Both declared display spectra contain finite values.",
        )
    )

    spectra_non_negative = bool(
        np.all(result.spectral_radiance_w_m3_sr >= 0.0)
        and np.all(result.spectral_exitance_w_m2_nm >= 0.0)
    )
    checks.append(
        ValidationCheck(
            name="planck_spectra_non_negative",
            passed=spectra_non_negative,
            observed=float(spectra_non_negative),
            expected=1.0,
            tolerance=0.0,
            comparison="exact",
            unit="dimensionless",
            explanation="Black-body spectral densities cannot be negative.",
        )
    )

    integrals_finite = bool(
        np.all(np.isfinite(result.numerical_integrated_radiance_w_m2_sr))
        and np.all(np.isfinite(result.numerical_integrated_exitance_w_m2))
    )
    checks.append(
        ValidationCheck(
            name="planck_integrals_finite",
            passed=integrals_finite,
            observed=float(integrals_finite),
            expected=1.0,
            tolerance=0.0,
            comparison="exact",
            unit="dimensionless",
            explanation="All wavelength integrals are finite.",
        )
    )

    expected_exitance_nm = (
        math.pi * result.spectral_radiance_w_m3_sr * 1.0e-9
    )
    absolute_difference = np.abs(
        result.spectral_exitance_w_m2_nm - expected_exitance_nm
    )
    pointwise_error = np.zeros_like(absolute_difference)
    np.divide(
        absolute_difference,
        np.abs(expected_exitance_nm),
        out=pointwise_error,
        where=(expected_exitance_nm != 0.0),
    )
    exitance_identity_error = float(np.max(pointwise_error))
    checks.append(
        ValidationCheck(
            name="planck_exitance_identity",
            passed=(
                exitance_identity_error
                <= configuration.exitance_identity_relative_tolerance
            ),
            observed=exitance_identity_error,
            expected=0.0,
            tolerance=configuration.exitance_identity_relative_tolerance,
            comparison="relative_error_le",
            unit="dimensionless",
            explanation=(
                "Spectral exitance equals pi times radiance with the per-nm "
                "unit conversion."
            ),
        )
    )

    for index, temperature in enumerate(result.temperatures_k):
        label = _temperature_label(float(temperature))

        peak_observed = float(result.numerical_peak_wavelength_m[index])
        peak_expected = float(result.wien_peak_wavelength_m[index])
        peak_error = _relative_error(peak_observed, peak_expected)
        checks.append(
            ValidationCheck(
                name=f"wien_peak_{label}",
                passed=(
                    peak_error <= configuration.wien_peak_relative_tolerance
                ),
                observed=peak_observed,
                expected=peak_expected,
                tolerance=configuration.wien_peak_relative_tolerance,
                comparison="relative_error_le",
                unit="m",
                explanation=(
                    "The numerical wavelength peak agrees with Wien's law."
                ),
            )
        )

        exitance_observed = float(
            result.numerical_integrated_exitance_w_m2[index]
        )
        exitance_expected = float(
            result.stefan_boltzmann_exitance_w_m2[index]
        )
        exitance_error = _relative_error(
            exitance_observed,
            exitance_expected,
        )
        checks.append(
            ValidationCheck(
                name=f"stefan_boltzmann_{label}",
                passed=(
                    exitance_error
                    <= configuration.stefan_boltzmann_relative_tolerance
                ),
                observed=exitance_observed,
                expected=exitance_expected,
                tolerance=configuration.stefan_boltzmann_relative_tolerance,
                comparison="relative_error_le",
                unit="W m^-2",
                explanation=(
                    "Integrated spectral exitance agrees with sigma T^4."
                ),
            )
        )

        radiance_observed = float(
            result.numerical_integrated_radiance_w_m2_sr[index]
        )
        radiance_expected = float(
            result.expected_integrated_radiance_w_m2_sr[index]
        )
        radiance_error = _relative_error(
            radiance_observed,
            radiance_expected,
        )
        checks.append(
            ValidationCheck(
                name=f"radiance_integral_{label}",
                passed=(
                    radiance_error
                    <= configuration.stefan_boltzmann_relative_tolerance
                ),
                observed=radiance_observed,
                expected=radiance_expected,
                tolerance=configuration.stefan_boltzmann_relative_tolerance,
                comparison="relative_error_le",
                unit="W m^-2 sr^-1",
                explanation=(
                    "Integrated spectral radiance agrees with sigma T^4/pi."
                ),
            )
        )

    frozen_checks = tuple(checks)
    return Task03ValidationReport(
        schema_version=configuration.schema_version,
        passed=all(check.passed for check in frozen_checks),
        checks=frozen_checks,
    )


__all__ = [
    "Task03ValidationReport",
    "ValidationCheck",
    "validate_planck_study",
]
