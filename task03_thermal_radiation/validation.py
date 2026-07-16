"""Structured validation for the deterministic Task 3 models."""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from task03_thermal_radiation.analysis import (
    EinsteinStudyResult,
    PlanckStudyResult,
)
from task03_thermal_radiation.configuration import Task03Configuration
from task03_thermal_radiation.models import einstein_molar_heat_capacity
from task03_thermal_radiation.reference import (
    dulong_petit_limit,
    einstein_anchor_ratio,
)


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


def _material_label(symbol: str) -> str:
    """Return a stable lower-case identifier for one chemical symbol."""

    label = "".join(
        character.lower() if character.isalnum() else "_"
        for character in symbol
    ).strip("_")
    if not label:
        raise ValueError("material symbol must contain an alphanumeric value")
    return label


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


def validate_einstein_study(
    result: EinsteinStudyResult,
    configuration: Task03Configuration | None = None,
) -> Task03ValidationReport:
    """Validate an Einstein study against every pre-declared Stage 7 check."""

    if not isinstance(result, EinsteinStudyResult):
        raise TypeError("result must be an EinsteinStudyResult")
    if configuration is None:
        configuration = result.configuration
    if not isinstance(configuration, Task03Configuration):
        raise TypeError("configuration must be a Task03Configuration")
    if configuration != result.configuration:
        raise ValueError("configuration must match the study result")

    checks: list[ValidationCheck] = []
    arrays = (
        result.einstein_temperatures_k,
        result.einstein_frequencies_hz,
        result.temperatures_k,
        result.molar_heat_capacity_j_mol_k,
        result.reduced_temperatures,
        result.normalized_heat_capacity,
    )
    all_finite = bool(all(np.all(np.isfinite(array)) for array in arrays))
    checks.append(
        ValidationCheck(
            name="einstein_results_finite",
            passed=all_finite,
            observed=float(all_finite),
            expected=1.0,
            tolerance=0.0,
            comparison="exact",
            unit="dimensionless",
            explanation="Every Einstein conversion and curve is finite.",
        )
    )

    limit = dulong_petit_limit()
    zero_temperature_indices = np.flatnonzero(result.temperatures_k == 0.0)
    zero_reduced_indices = np.flatnonzero(result.reduced_temperatures == 0.0)
    if zero_temperature_indices.size != 1 or zero_reduced_indices.size != 1:
        raise ValueError("Einstein study grids must each contain exactly one zero")
    zero_capacity = np.concatenate(
        (
            result.molar_heat_capacity_j_mol_k[
                :,
                int(zero_temperature_indices[0]),
            ],
            (
                result.normalized_heat_capacity[
                    :,
                    int(zero_reduced_indices[0]),
                ]
                * limit
            ),
        )
    )
    zero_error = float(np.max(np.abs(zero_capacity)))
    checks.append(
        ValidationCheck(
            name="einstein_zero_limit",
            passed=(zero_error == 0.0),
            observed=zero_error,
            expected=0.0,
            tolerance=0.0,
            comparison="absolute_error_le",
            unit="J mol^-1 K^-1",
            explanation="The continuous Einstein limit is exactly zero at T=0.",
        )
    )

    normalized_principal = result.molar_heat_capacity_j_mol_k / limit
    lower_violation = max(0.0, -float(np.min(normalized_principal)))
    upper_violation = max(0.0, float(np.max(normalized_principal)) - 1.0)
    normalized_lower_violation = max(
        0.0,
        -float(np.min(result.normalized_heat_capacity)),
    )
    normalized_upper_violation = max(
        0.0,
        float(np.max(result.normalized_heat_capacity)) - 1.0,
    )
    bound_violation = max(
        lower_violation,
        upper_violation,
        normalized_lower_violation,
        normalized_upper_violation,
    )
    checks.append(
        ValidationCheck(
            name="einstein_physical_bounds",
            passed=(
                bound_violation <= configuration.einstein_bound_relative_slack
            ),
            observed=bound_violation,
            expected=0.0,
            tolerance=configuration.einstein_bound_relative_slack,
            comparison="relative_slack_le",
            unit="dimensionless",
            explanation="Both declared curve sets remain between zero and 3R.",
        )
    )

    principal_differences = np.diff(
        result.molar_heat_capacity_j_mol_k,
        axis=1,
    )
    normalized_differences = np.diff(
        result.normalized_heat_capacity * limit,
        axis=1,
    )
    monotonic_violation = max(
        0.0,
        -float(np.min(principal_differences)),
        -float(np.min(normalized_differences)),
    )
    checks.append(
        ValidationCheck(
            name="einstein_monotonicity",
            passed=(
                monotonic_violation
                <= configuration.einstein_monotonic_absolute_slack
            ),
            observed=monotonic_violation,
            expected=0.0,
            tolerance=configuration.einstein_monotonic_absolute_slack,
            comparison="absolute_slack_le",
            unit="J mol^-1 K^-1",
            explanation="Heat capacity is non-decreasing on both declared grids.",
        )
    )

    anchor_indices = np.flatnonzero(result.reduced_temperatures == 1.0)
    if anchor_indices.size != 1:
        raise ValueError(
            "Einstein reduced-temperature grid must contain exactly one anchor"
        )
    anchor_observed = result.normalized_heat_capacity[
        :,
        int(anchor_indices[0]),
    ]
    anchor_expected = einstein_anchor_ratio()
    anchor_error = float(np.max(np.abs(anchor_observed - anchor_expected)))
    checks.append(
        ValidationCheck(
            name="einstein_anchor_ratio",
            passed=(
                anchor_error <= configuration.einstein_anchor_absolute_tolerance
            ),
            observed=anchor_error,
            expected=0.0,
            tolerance=configuration.einstein_anchor_absolute_tolerance,
            comparison="absolute_error_le",
            unit="dimensionless",
            explanation="At T=T_E, every curve matches the analytical ratio.",
        )
    )

    high_temperature_capacity = einstein_molar_heat_capacity(
        100.0 * result.einstein_temperatures_k,
        result.einstein_temperatures_k,
    )
    high_temperature_error = float(
        np.max(np.abs(high_temperature_capacity - limit) / limit)
    )
    checks.append(
        ValidationCheck(
            name="einstein_high_temperature_limit",
            passed=(
                high_temperature_error
                <= configuration.einstein_high_temperature_relative_tolerance
            ),
            observed=high_temperature_error,
            expected=0.0,
            tolerance=(
                configuration.einstein_high_temperature_relative_tolerance
            ),
            comparison="relative_error_le",
            unit="dimensionless",
            explanation="At T=100T_E, heat capacity agrees with the 3R limit.",
        )
    )

    for index, material in enumerate(result.materials):
        observed_frequency = float(result.einstein_frequencies_hz[index] / 1.0e13)
        expected_frequency = material.official_frequency_1e13_hz
        passed = round(observed_frequency, 4) == expected_frequency
        checks.append(
            ValidationCheck(
                name=f"einstein_frequency_{_material_label(material.symbol)}",
                passed=passed,
                observed=observed_frequency,
                expected=expected_frequency,
                tolerance=0.0,
                comparison="equal_after_4_decimal_rounding",
                unit="1e13 Hz",
                explanation=(
                    "Calculated frequency reproduces the official displayed "
                    f"value for {material.symbol}."
                ),
            )
        )

    collapse_error = float(
        np.max(
            np.abs(
                result.normalized_heat_capacity
                - result.normalized_heat_capacity[0:1, :]
            )
        )
    )
    checks.append(
        ValidationCheck(
            name="einstein_normalized_collapse",
            passed=(
                collapse_error
                <= configuration.einstein_normalized_collapse_tolerance
            ),
            observed=collapse_error,
            expected=0.0,
            tolerance=configuration.einstein_normalized_collapse_tolerance,
            comparison="maximum_absolute_difference_le",
            unit="dimensionless",
            explanation=(
                "All materials collapse onto one C_V/(3R) versus T/T_E curve."
            ),
        )
    )

    frozen_checks = tuple(checks)
    return Task03ValidationReport(
        schema_version=configuration.schema_version,
        passed=all(check.passed for check in frozen_checks),
        checks=frozen_checks,
    )


def validate_task03(
    planck_result: PlanckStudyResult,
    einstein_result: EinsteinStudyResult,
    configuration: Task03Configuration | None = None,
) -> Task03ValidationReport:
    """Return one ordered report containing all Planck and Einstein checks."""

    if not isinstance(planck_result, PlanckStudyResult):
        raise TypeError("planck_result must be a PlanckStudyResult")
    if not isinstance(einstein_result, EinsteinStudyResult):
        raise TypeError("einstein_result must be an EinsteinStudyResult")
    if configuration is None:
        configuration = planck_result.configuration
    if not isinstance(configuration, Task03Configuration):
        raise TypeError("configuration must be a Task03Configuration")
    if configuration != planck_result.configuration:
        raise ValueError("configuration must match the Planck study result")
    if configuration != einstein_result.configuration:
        raise ValueError("configuration must match the Einstein study result")

    planck_report = validate_planck_study(planck_result, configuration)
    einstein_report = validate_einstein_study(einstein_result, configuration)
    checks = planck_report.checks + einstein_report.checks
    return Task03ValidationReport(
        schema_version=configuration.schema_version,
        passed=all(check.passed for check in checks),
        checks=checks,
    )


__all__ = [
    "Task03ValidationReport",
    "ValidationCheck",
    "validate_einstein_study",
    "validate_planck_study",
    "validate_task03",
]
