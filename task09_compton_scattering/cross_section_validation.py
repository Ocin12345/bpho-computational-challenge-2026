"""Structured validation for the separately labelled Klein–Nishina extension."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Tuple

import numpy as np

from task09_compton_scattering.configuration import (
    DEFAULT_CONFIGURATION,
    Task09Configuration,
)
from task09_compton_scattering.constants import (
    BARN_M2,
    CLASSICAL_ELECTRON_RADIUS_M,
    THOMSON_CROSS_SECTION_M2,
)
from task09_compton_scattering.cross_section import KleinNishinaStudy
from task09_compton_scattering.cross_section_reference import (
    reference_total_cross_section_m2,
)
from task09_compton_scattering.validation import ValidationCheck


CROSS_SECTION_VALIDATION_SCHEMA_VERSION = "task09-cross-section-validation-v1"
CROSS_SECTION_ARRAY_FIELDS = (
    "incident_energy_kev",
    "theta_deg",
    "scattered_to_incident_energy_ratio",
    "differential_cross_section_m2_sr",
    "differential_cross_section_barn_sr",
    "relative_differential_cross_section",
    "theta_density_m2_rad",
    "theta_pdf_rad_inv",
    "total_cross_section_m2",
    "total_cross_section_barn",
)


@dataclass(frozen=True)
class CrossSectionValidationReport:
    """Extension checks bound to one cross-section study digest."""

    schema_version: str
    study_digest: str
    checks: Tuple[ValidationCheck, ...]

    def __post_init__(self) -> None:
        if self.schema_version != CROSS_SECTION_VALIDATION_SCHEMA_VERSION:
            raise ValueError("invalid cross-section validation schema")
        if (
            not isinstance(self.study_digest, str)
            or len(self.study_digest) != 64
            or any(character not in "0123456789abcdef" for character in self.study_digest)
        ):
            raise ValueError("study_digest must be a lowercase SHA-256 digest")
        checks = tuple(self.checks)
        if not checks or any(not isinstance(check, ValidationCheck) for check in checks):
            raise TypeError("checks must contain ValidationCheck records")
        if len({check.name for check in checks}) != len(checks):
            raise ValueError("cross-section check names must be unique")
        object.__setattr__(self, "checks", checks)

    @property
    def passed(self) -> bool:
        return all(check.passed for check in self.checks)

    @property
    def failed_checks(self) -> Tuple[ValidationCheck, ...]:
        return tuple(check for check in self.checks if not check.passed)


def cross_section_study_digest(study: KleinNishinaStudy) -> str:
    """Return a stable digest of the complete extension study."""

    if not isinstance(study, KleinNishinaStudy):
        raise TypeError("study must be a KleinNishinaStudy")
    digest = hashlib.sha256(b"task09-cross-section-study-v1")
    for name in CROSS_SECTION_ARRAY_FIELDS:
        array = np.ascontiguousarray(getattr(study, name))
        digest.update(name.encode("ascii"))
        digest.update(array.dtype.str.encode("ascii"))
        digest.update(str(array.shape).encode("ascii"))
        digest.update(array.tobytes())
    return digest.hexdigest()


def _check(
    *,
    name: str,
    observed: float,
    expected: float,
    tolerance: float,
    passed: bool,
    unit: str,
    comparison: str,
    explanation: str,
) -> ValidationCheck:
    return ValidationCheck(
        name=name,
        passed=bool(passed),
        observed=float(observed),
        expected=float(expected),
        unit=unit,
        comparison=comparison,
        tolerance=float(tolerance),
        explanation=explanation,
    )


def _absolute(
    *,
    name: str,
    error: float,
    tolerance: float,
    unit: str,
    explanation: str,
) -> ValidationCheck:
    normalized = abs(float(error))
    if not np.isfinite(normalized):
        normalized = 1.0e300
    return _check(
        name=name,
        observed=normalized,
        expected=0.0,
        tolerance=tolerance,
        passed=normalized <= tolerance,
        unit=unit,
        comparison="absolute_error_lte",
        explanation=explanation,
    )


def _lower(
    *,
    name: str,
    observed: float,
    expected: float,
    tolerance: float,
    unit: str,
    explanation: str,
) -> ValidationCheck:
    return _check(
        name=name,
        observed=observed,
        expected=expected,
        tolerance=tolerance,
        passed=observed + tolerance >= expected,
        unit=unit,
        comparison="greater_than_or_equal",
        explanation=explanation,
    )


def _upper(
    *,
    name: str,
    observed: float,
    expected: float,
    tolerance: float,
    unit: str,
    explanation: str,
) -> ValidationCheck:
    return _check(
        name=name,
        observed=observed,
        expected=expected,
        tolerance=tolerance,
        passed=observed <= expected + tolerance,
        unit=unit,
        comparison="less_than_or_equal",
        explanation=explanation,
    )


def _max_relative(observed: np.ndarray, expected: np.ndarray) -> float:
    return float(
        np.max(
            np.abs(observed - expected) / np.maximum(np.abs(expected), 1.0e-300)
        )
    )


def validate_cross_section_study(
    study: KleinNishinaStudy,
    configuration: Task09Configuration = DEFAULT_CONFIGURATION,
) -> CrossSectionValidationReport:
    """Validate the official-energy Klein–Nishina extension without repair."""

    if not isinstance(study, KleinNishinaStudy):
        raise TypeError("study must be a KleinNishinaStudy")
    if not isinstance(configuration, Task09Configuration):
        raise TypeError("configuration must be a Task09Configuration")

    checks = []
    energies = np.asarray(configuration.incident_energies_kev, dtype=np.float64)
    theta = np.linspace(
        configuration.angle_minimum_deg,
        configuration.angle_maximum_deg,
        configuration.angle_point_count,
        dtype=np.float64,
    )
    expected_energy, expected_theta = np.broadcast_arrays(
        energies[:, None], theta[None, :]
    )
    checks.extend(
        (
            _absolute(
                name="official_energy_grid",
                error=float(np.max(np.abs(study.incident_energy_kev - expected_energy))),
                tolerance=0.0,
                unit="keV",
                explanation="The extension uses the same five official energies.",
            ),
            _absolute(
                name="full_angle_grid",
                error=float(np.max(np.abs(study.theta_deg - expected_theta))),
                tolerance=0.0,
                unit="degree",
                explanation="The extension uses the same inclusive angle grid.",
            ),
            _check(
                name="all_cross_section_arrays_finite",
                observed=float(
                    sum(
                        np.count_nonzero(~np.isfinite(getattr(study, name)))
                        for name in CROSS_SECTION_ARRAY_FIELDS
                    )
                ),
                expected=0.0,
                tolerance=0.0,
                passed=all(
                    np.all(np.isfinite(getattr(study, name)))
                    for name in CROSS_SECTION_ARRAY_FIELDS
                ),
                unit="count",
                comparison="exact_equal",
                explanation="Every extension value is finite.",
            ),
        )
    )

    for name, array, unit in (
        (
            "differential_cross_section_nonnegative",
            study.differential_cross_section_m2_sr,
            "m^2 sr^-1",
        ),
        (
            "relative_cross_section_nonnegative",
            study.relative_differential_cross_section,
            "dimensionless",
        ),
        ("theta_pdf_nonnegative", study.theta_pdf_rad_inv, "rad^-1"),
    ):
        checks.append(
            _lower(
                name=name,
                observed=float(np.min(array)),
                expected=0.0,
                tolerance=0.0,
                unit=unit,
                explanation="A scattering cross-section or density cannot be negative.",
            )
        )

    checks.extend(
        (
            _absolute(
                name="forward_differential_cross_section",
                error=float(
                    np.max(
                        np.abs(
                            study.differential_cross_section_m2_sr[:, 0]
                            - CLASSICAL_ELECTRON_RADIUS_M**2
                        )
                    )
                ),
                tolerance=1.0e-44,
                unit="m^2 sr^-1",
                explanation="All energies share the Klein–Nishina forward value r_e^2.",
            ),
            _absolute(
                name="forward_relative_cross_section",
                error=float(
                    np.max(
                        np.abs(study.relative_differential_cross_section[:, 0] - 1.0)
                    )
                ),
                tolerance=2.0e-15,
                unit="dimensionless",
                explanation="Every relative differential curve begins at one.",
            ),
            _absolute(
                name="forward_theta_density_zero",
                error=float(np.max(np.abs(study.theta_density_m2_rad[:, 0]))),
                tolerance=0.0,
                unit="m^2 rad^-1",
                explanation="The forward polar ring has zero solid-angle area.",
            ),
            _absolute(
                name="backscatter_theta_density_zero",
                error=float(np.max(np.abs(study.theta_density_m2_rad[:, -1]))),
                tolerance=0.0,
                unit="m^2 rad^-1",
                explanation="The backscatter polar ring has zero solid-angle area.",
            ),
        )
    )

    row_totals = study.total_cross_section_m2[:, 0]
    checks.extend(
        (
            _lower(
                name="total_cross_section_positive",
                observed=float(np.min(row_totals)),
                expected=0.0,
                tolerance=0.0,
                unit="m^2",
                explanation="Every total free-electron cross-section is positive.",
            ),
            _upper(
                name="total_cross_section_below_thomson",
                observed=float(np.max(row_totals)),
                expected=THOMSON_CROSS_SECTION_M2,
                tolerance=0.0,
                unit="m^2",
                explanation="Nonzero-energy Klein–Nishina totals lie below Thomson.",
            ),
            _lower(
                name="total_cross_section_energy_decrease",
                observed=float(np.min(-np.diff(row_totals))),
                expected=0.0,
                tolerance=0.0,
                unit="m^2",
                explanation="Total cross-section decreases over the official energies.",
            ),
            _lower(
                name="backscatter_differential_energy_decrease",
                observed=float(
                    np.min(-np.diff(study.differential_cross_section_m2_sr[:, -1]))
                ),
                expected=0.0,
                tolerance=0.0,
                unit="m^2 sr^-1",
                explanation="High-energy backscatter is increasingly suppressed.",
            ),
            _upper(
                name="differential_not_above_forward",
                observed=float(np.max(study.relative_differential_cross_section)),
                expected=1.0,
                tolerance=2.0e-15,
                unit="dimensionless",
                explanation="The forward direction is the differential maximum here.",
            ),
        )
    )

    quadrature_totals = np.asarray(
        [
            reference_total_cross_section_m2(
                float(energy), configuration.cross_section_quadrature_order
            )
            for energy in energies
        ]
    )
    checks.append(
        _absolute(
            name="analytical_total_vs_quadrature",
            error=_max_relative(row_totals, quadrature_totals),
            tolerance=configuration.cross_section_relative_tolerance,
            unit="relative error",
            explanation="Closed-form totals agree with independent solid-angle quadrature.",
        )
    )

    theta_rad = np.radians(theta)
    pdf_integrals = np.trapezoid(study.theta_pdf_rad_inv, theta_rad, axis=1)
    checks.append(
        _absolute(
            name="theta_pdf_normalization",
            error=float(np.max(np.abs(pdf_integrals - 1.0))),
            tolerance=5.0e-6,
            unit="probability",
            explanation="The plotted polar-angle density integrates to unity.",
        )
    )
    right_angle_index = configuration.angle_point_count // 2
    forward_probabilities = np.trapezoid(
        study.theta_pdf_rad_inv[:, : right_angle_index + 1],
        theta_rad[: right_angle_index + 1],
        axis=1,
    )
    checks.extend(
        (
            _lower(
                name="forward_hemisphere_probability_ordering",
                observed=float(np.min(np.diff(forward_probabilities))),
                expected=0.0,
                tolerance=2.0e-7,
                unit="probability",
                explanation="Higher-energy scattering becomes more forward weighted.",
            ),
            _lower(
                name="one_mev_forward_bias",
                observed=float(forward_probabilities[-1]),
                expected=0.70,
                tolerance=0.0,
                unit="probability",
                explanation="At 1 MeV most free-electron scattering lies in the forward hemisphere.",
            ),
        )
    )

    low_energy_total = reference_total_cross_section_m2(1.0e-6, 256)
    checks.append(
        _absolute(
            name="independent_thomson_limit",
            error=low_energy_total / THOMSON_CROSS_SECTION_M2 - 1.0,
            tolerance=1.0e-8,
            unit="relative error",
            explanation="Independent quadrature approaches Thomson at negligible photon energy.",
        )
    )

    checks.extend(
        (
            _absolute(
                name="differential_barn_conversion",
                error=_max_relative(
                    study.differential_cross_section_barn_sr,
                    study.differential_cross_section_m2_sr / BARN_M2,
                ),
                tolerance=2.0e-15,
                unit="relative error",
                explanation="Differential values use the exact barn conversion.",
            ),
            _absolute(
                name="total_barn_conversion",
                error=_max_relative(
                    study.total_cross_section_barn,
                    study.total_cross_section_m2 / BARN_M2,
                ),
                tolerance=2.0e-15,
                unit="relative error",
                explanation="Total values use the exact barn conversion.",
            ),
            _absolute(
                name="total_constant_across_angle",
                error=float(
                    np.max(
                        np.abs(study.total_cross_section_m2 - row_totals[:, None])
                    )
                ),
                tolerance=0.0,
                unit="m^2",
                explanation="Each total is broadcast unchanged over its angle row.",
            ),
            _absolute(
                name="relative_differential_identity",
                error=_max_relative(
                    study.relative_differential_cross_section,
                    study.differential_cross_section_m2_sr
                    / CLASSICAL_ELECTRON_RADIUS_M**2,
                ),
                tolerance=2.0e-15,
                unit="relative error",
                explanation="Relative curves are normalized to the common forward value.",
            ),
            _absolute(
                name="theta_density_identity",
                error=_max_relative(
                    study.theta_density_m2_rad[:, 1:-1],
                    2.0
                    * np.pi
                    * np.sin(np.radians(study.theta_deg[:, 1:-1]))
                    * study.differential_cross_section_m2_sr[:, 1:-1],
                ),
                tolerance=2.0e-15,
                unit="relative error",
                explanation="Polar density includes the complete azimuthal Jacobian.",
            ),
            _absolute(
                name="theta_pdf_identity",
                error=_max_relative(
                    study.theta_pdf_rad_inv[:, 1:-1],
                    study.theta_density_m2_rad[:, 1:-1]
                    / study.total_cross_section_m2[:, 1:-1],
                ),
                tolerance=2.0e-15,
                unit="relative error",
                explanation="The polar PDF is density divided by total cross-section.",
            ),
        )
    )

    expected_total_barns = np.asarray(
        [
            0.561506943706434,
            0.492748487639704,
            0.406482469509729,
            0.289166317232033,
            0.211207882544261,
        ]
    )
    checks.append(
        _absolute(
            name="official_energy_total_anchors",
            error=_max_relative(study.total_cross_section_barn[:, 0], expected_total_barns),
            tolerance=5.0e-13,
            unit="relative error",
            explanation="Five independently frozen total cross-sections agree.",
        )
    )
    checks.extend(
        (
            _lower(
                name="scattered_energy_ratio_lower_bound",
                observed=float(np.min(study.scattered_to_incident_energy_ratio)),
                expected=0.0,
                tolerance=0.0,
                unit="dimensionless",
                explanation="A scattered photon retains positive energy.",
            ),
            _upper(
                name="scattered_energy_ratio_upper_bound",
                observed=float(np.max(study.scattered_to_incident_energy_ratio)),
                expected=1.0,
                tolerance=0.0,
                unit="dimensionless",
                explanation="A free stationary electron cannot increase photon energy.",
            ),
            _lower(
                name="scattered_ratio_angle_decrease",
                observed=float(
                    np.min(-np.diff(study.scattered_to_incident_energy_ratio, axis=1))
                ),
                expected=0.0,
                tolerance=2.0e-15,
                unit="dimensionless",
                explanation="Scattered photon energy decreases with deflection angle.",
            ),
        )
    )

    return CrossSectionValidationReport(
        schema_version=CROSS_SECTION_VALIDATION_SCHEMA_VERSION,
        study_digest=cross_section_study_digest(study),
        checks=tuple(checks),
    )


__all__ = [
    "CROSS_SECTION_ARRAY_FIELDS",
    "CrossSectionValidationReport",
    "cross_section_study_digest",
    "validate_cross_section_study",
]
