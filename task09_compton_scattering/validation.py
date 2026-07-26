"""Independent structured validation for the complete Task 9 study."""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from typing import Callable, Tuple

import numpy as np

from task09_compton_scattering.analysis import Task09StudyResult
from task09_compton_scattering.configuration import (
    DEFAULT_CONFIGURATION,
    Task09Configuration,
)
from task09_compton_scattering.constants import (
    ELECTRON_REST_ENERGY_KEV,
    SPEED_OF_LIGHT_M_S,
)
from task09_compton_scattering.reference import reference_kinematics


VALIDATION_SCHEMA_VERSION = "task09-validation-v1"

STUDY_ARRAY_FIELDS = (
    "incident_energies_kev",
    "theta_axis_deg",
    "incident_energy_kev",
    "theta_deg",
    "alpha",
    "incident_wavelength_m",
    "wavelength_shift_m",
    "fractional_wavelength_shift",
    "scattered_wavelength_m",
    "scattered_energy_kev",
    "electron_kinetic_energy_kev",
    "electron_gamma",
    "electron_beta",
    "electron_speed_m_s",
    "electron_pc_kev",
    "electron_recoil_angle_deg",
    "electron_recoil_direction_defined",
)


@dataclass(frozen=True)
class ValidationCheck:
    """One machine-readable scientific acceptance check."""

    name: str
    passed: bool
    observed: float
    expected: float
    unit: str
    comparison: str
    tolerance: float
    explanation: str

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name:
            raise ValueError("check name must be non-empty text")
        if not isinstance(self.passed, bool):
            raise TypeError("passed must be boolean")
        for field_name in ("observed", "expected", "tolerance"):
            value = float(getattr(self, field_name))
            if not math.isfinite(value):
                raise ValueError(f"{field_name} must be finite")
            object.__setattr__(self, field_name, value)
        if self.tolerance < 0.0:
            raise ValueError("tolerance must be non-negative")
        for field_name in ("unit", "comparison", "explanation"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value:
                raise ValueError(f"{field_name} must be non-empty text")


@dataclass(frozen=True)
class Task09ValidationReport:
    """Complete report bound to one immutable study digest."""

    schema_version: str
    study_digest: str
    checks: Tuple[ValidationCheck, ...]

    def __post_init__(self) -> None:
        if self.schema_version != VALIDATION_SCHEMA_VERSION:
            raise ValueError("invalid validation schema version")
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
            raise ValueError("validation check names must be unique")
        object.__setattr__(self, "checks", checks)

    @property
    def passed(self) -> bool:
        return all(check.passed for check in self.checks)

    @property
    def failed_checks(self) -> Tuple[ValidationCheck, ...]:
        return tuple(check for check in self.checks if not check.passed)


def task09_study_digest(study: Task09StudyResult) -> str:
    """Return a stable digest of every scientific array in the study."""

    if not isinstance(study, Task09StudyResult):
        raise TypeError("study must be a Task09StudyResult")
    digest = hashlib.sha256(study.schema_version.encode("utf-8"))
    for name in STUDY_ARRAY_FIELDS:
        array = np.ascontiguousarray(getattr(study, name))
        digest.update(name.encode("ascii"))
        digest.update(array.dtype.str.encode("ascii"))
        digest.update(str(array.shape).encode("ascii"))
        digest.update(array.tobytes())
    return digest.hexdigest()


def _safe_error(value: float) -> float:
    normalized = abs(float(value))
    return normalized if math.isfinite(normalized) else 1.0e300


def _absolute_check(
    *,
    name: str,
    error: float,
    tolerance: float,
    unit: str,
    explanation: str,
) -> ValidationCheck:
    normalized = _safe_error(error)
    return ValidationCheck(
        name=name,
        passed=normalized <= tolerance,
        observed=normalized,
        expected=0.0,
        unit=unit,
        comparison="absolute_error_lte",
        tolerance=tolerance,
        explanation=explanation,
    )


def _exact_check(*, name: str, mismatches: int, explanation: str) -> ValidationCheck:
    count = int(mismatches)
    return ValidationCheck(
        name=name,
        passed=count == 0,
        observed=float(count),
        expected=0.0,
        unit="count",
        comparison="exact_equal",
        tolerance=0.0,
        explanation=explanation,
    )


def _bound_check(
    *,
    name: str,
    observed: float,
    expected: float,
    tolerance: float,
    lower: bool,
    unit: str,
    explanation: str,
) -> ValidationCheck:
    value = float(observed)
    passed = value + tolerance >= expected if lower else value <= expected + tolerance
    return ValidationCheck(
        name=name,
        passed=bool(passed),
        observed=value,
        expected=expected,
        unit=unit,
        comparison="greater_than_or_equal" if lower else "less_than_or_equal",
        tolerance=tolerance,
        explanation=explanation,
    )


def _max_relative_error(observed: np.ndarray, expected: np.ndarray) -> float:
    scale = np.maximum(np.abs(expected), 1.0e-300)
    return float(np.max(np.abs(observed - expected) / scale))


def _reference_matrix(
    study: Task09StudyResult,
    extractor: Callable[[object], float],
) -> np.ndarray:
    values = np.fromiter(
        (
            extractor(reference_kinematics(float(energy), float(theta)))
            for energy, theta in zip(
                study.incident_energy_kev.flat,
                study.theta_deg.flat,
            )
        ),
        dtype=np.float64,
        count=study.row_count,
    )
    return values.reshape(study.incident_energy_kev.shape)


def validate_task09(
    study: Task09StudyResult,
    configuration: Task09Configuration = DEFAULT_CONFIGURATION,
) -> Task09ValidationReport:
    """Return all pre-declared checks without repairing the supplied study."""

    if not isinstance(study, Task09StudyResult):
        raise TypeError("study must be a Task09StudyResult")
    if not isinstance(configuration, Task09Configuration):
        raise TypeError("configuration must be a Task09Configuration")

    checks = []
    absolute_tolerance = configuration.numerical_absolute_tolerance
    relative_tolerance = configuration.numerical_relative_tolerance
    conservation_tolerance = configuration.conservation_relative_tolerance

    expected_energies = np.asarray(configuration.incident_energies_kev)
    expected_theta = np.linspace(
        configuration.angle_minimum_deg,
        configuration.angle_maximum_deg,
        configuration.angle_point_count,
        dtype=np.float64,
    )
    expected_energy_grid, expected_theta_grid = np.broadcast_arrays(
        expected_energies[:, None],
        expected_theta[None, :],
    )
    checks.extend(
        (
            _exact_check(
                name="official_energy_axis",
                mismatches=int(
                    not np.array_equal(study.incident_energies_kev, expected_energies)
                ),
                explanation="The study uses the five energies shown by the official brief.",
            ),
            _exact_check(
                name="full_angle_axis",
                mismatches=int(not np.array_equal(study.theta_axis_deg, expected_theta)),
                explanation="The inclusive 0–180 degree axis has the frozen spacing.",
            ),
            _exact_check(
                name="broadcast_energy_grid",
                mismatches=int(
                    not np.array_equal(study.incident_energy_kev, expected_energy_grid)
                ),
                explanation="Every study row carries the correct incident energy.",
            ),
            _exact_check(
                name="broadcast_angle_grid",
                mismatches=int(not np.array_equal(study.theta_deg, expected_theta_grid)),
                explanation="Every study column carries the correct scattering angle.",
            ),
            _exact_check(
                name="all_scientific_arrays_finite",
                mismatches=sum(
                    int(np.count_nonzero(~np.isfinite(getattr(study, name))))
                    for name in STUDY_ARRAY_FIELDS
                    if name != "electron_recoil_direction_defined"
                ),
                explanation="Every stored numerical kinematic value is finite.",
            ),
        )
    )

    expected_direction = np.ones(study.theta_deg.shape, dtype=np.bool_)
    expected_direction[:, 0] = False
    checks.append(
        _exact_check(
            name="recoil_direction_validity",
            mismatches=int(
                np.count_nonzero(
                    study.electron_recoil_direction_defined != expected_direction
                )
            ),
            explanation="Only the zero-momentum forward endpoint has undefined direction.",
        )
    )

    forward_fields = (
        ("forward_fractional_shift", study.fractional_wavelength_shift[:, 0], 0.0),
        (
            "forward_scattered_energy",
            study.scattered_energy_kev[:, 0],
            study.incident_energies_kev,
        ),
        ("forward_kinetic_energy", study.electron_kinetic_energy_kev[:, 0], 0.0),
        ("forward_beta", study.electron_beta[:, 0], 0.0),
        ("forward_momentum", study.electron_pc_kev[:, 0], 0.0),
        ("forward_angle_plot_limit", study.electron_recoil_angle_deg[:, 0], 90.0),
        ("backscatter_recoil_angle", study.electron_recoil_angle_deg[:, -1], 0.0),
    )
    for name, observed, expected in forward_fields:
        checks.append(
            _absolute_check(
                name=name,
                error=float(np.max(np.abs(observed - expected))),
                tolerance=absolute_tolerance,
                unit="mixed",
                explanation="The analytical endpoint convention is reproduced exactly.",
            )
        )

    checks.extend(
        (
            _bound_check(
                name="fractional_shift_lower_bound",
                observed=float(np.min(study.fractional_wavelength_shift)),
                expected=0.0,
                tolerance=absolute_tolerance,
                lower=True,
                unit="dimensionless",
                explanation="Compton wavelength shift is non-negative.",
            ),
            _bound_check(
                name="electron_beta_lower_bound",
                observed=float(np.min(study.electron_beta)),
                expected=0.0,
                tolerance=absolute_tolerance,
                lower=True,
                unit="v/c",
                explanation="Electron recoil speed is non-negative.",
            ),
            _bound_check(
                name="electron_beta_upper_bound",
                observed=float(np.max(study.electron_beta)),
                expected=1.0,
                tolerance=0.0,
                lower=False,
                unit="v/c",
                explanation="Every massive-electron recoil remains subluminal.",
            ),
            _bound_check(
                name="recoil_angle_lower_bound",
                observed=float(np.min(study.electron_recoil_angle_deg)),
                expected=0.0,
                tolerance=absolute_tolerance,
                lower=True,
                unit="degree",
                explanation="The recoil-angle magnitude is non-negative.",
            ),
            _bound_check(
                name="recoil_angle_upper_bound",
                observed=float(np.max(study.electron_recoil_angle_deg)),
                expected=90.0,
                tolerance=absolute_tolerance,
                lower=False,
                unit="degree",
                explanation="The recoil-angle magnitude does not exceed its forward limit.",
            ),
            _bound_check(
                name="scattered_energy_positive",
                observed=float(np.min(study.scattered_energy_kev)),
                expected=0.0,
                tolerance=0.0,
                lower=True,
                unit="keV",
                explanation="The scattered photon retains positive energy.",
            ),
        )
    )

    for name, differences, upper_bound, unit, explanation in (
        (
            "fractional_shift_angle_monotonic",
            np.diff(study.fractional_wavelength_shift, axis=1),
            0.0,
            "dimensionless",
            "Wavelength shift never decreases as scattering angle increases.",
        ),
        (
            "electron_speed_angle_monotonic",
            np.diff(study.electron_beta, axis=1),
            0.0,
            "v/c",
            "Recoil speed never decreases as scattering angle increases.",
        ),
        (
            "recoil_angle_monotonic_decrease",
            -np.diff(study.electron_recoil_angle_deg, axis=1),
            0.0,
            "degree",
            "Recoil angle never increases as photon scattering angle increases.",
        ),
    ):
        checks.append(
            _bound_check(
                name=name,
                observed=float(np.min(differences)),
                expected=upper_bound,
                tolerance=2.0e-13,
                lower=True,
                unit=unit,
                explanation=explanation,
            )
        )

    energy_scale = np.maximum(study.incident_energy_kev, 1.0)
    checks.append(
        _absolute_check(
            name="energy_conservation",
            error=float(
                np.max(
                    np.abs(
                        study.incident_energy_kev
                        - study.scattered_energy_kev
                        - study.electron_kinetic_energy_kev
                    )
                    / energy_scale
                )
            ),
            tolerance=conservation_tolerance,
            unit="relative residual",
            explanation="Photon energy loss equals electron kinetic energy.",
        )
    )
    checks.append(
        _absolute_check(
            name="wavelength_shift_identity",
            error=_max_relative_error(
                study.scattered_wavelength_m,
                study.incident_wavelength_m + study.wavelength_shift_m,
            ),
            tolerance=relative_tolerance,
            unit="relative error",
            explanation="Scattered wavelength equals incident wavelength plus shift.",
        )
    )
    checks.append(
        _absolute_check(
            name="fractional_shift_identity",
            error=float(
                np.max(
                    np.abs(
                        study.fractional_wavelength_shift
                        - study.wavelength_shift_m / study.incident_wavelength_m
                    )
                )
            ),
            tolerance=absolute_tolerance,
            unit="dimensionless",
            explanation="Stored fractional shift is the wavelength ratio.",
        )
    )
    checks.append(
        _absolute_check(
            name="alpha_energy_identity",
            error=float(
                np.max(
                    np.abs(
                        study.alpha
                        - study.incident_energy_kev / ELECTRON_REST_ENERGY_KEV
                    )
                )
            ),
            tolerance=absolute_tolerance,
            unit="dimensionless",
            explanation="Dimensionless energy is E divided by electron rest energy.",
        )
    )
    checks.append(
        _absolute_check(
            name="gamma_kinetic_identity",
            error=float(
                np.max(
                    np.abs(
                        study.electron_gamma
                        - 1.0
                        - study.electron_kinetic_energy_kev
                        / ELECTRON_REST_ENERGY_KEV
                    )
                )
            ),
            tolerance=absolute_tolerance,
            unit="dimensionless",
            explanation="Lorentz factor follows the electron kinetic energy.",
        )
    )
    beta_reference = np.sqrt(
        np.maximum(
            (study.electron_gamma - 1.0)
            * (study.electron_gamma + 1.0)
            / np.square(study.electron_gamma),
            0.0,
        )
    )
    checks.append(
        _absolute_check(
            name="beta_gamma_identity",
            error=float(np.max(np.abs(study.electron_beta - beta_reference))),
            tolerance=absolute_tolerance,
            unit="v/c",
            explanation="Recoil speed agrees with its Lorentz-factor identity.",
        )
    )
    checks.append(
        _absolute_check(
            name="speed_beta_identity",
            error=_max_relative_error(
                study.electron_speed_m_s,
                study.electron_beta * SPEED_OF_LIGHT_M_S,
            ),
            tolerance=relative_tolerance,
            unit="relative error",
            explanation="SI speed is beta times the exact speed of light.",
        )
    )

    theta_rad = np.radians(study.theta_deg)
    photon_x = study.incident_energy_kev - study.scattered_energy_kev * np.cos(
        theta_rad
    )
    photon_y = study.scattered_energy_kev * np.sin(theta_rad)
    photon_y[:, (0, -1)] = 0.0
    expected_pc = np.hypot(photon_x, photon_y)
    checks.append(
        _absolute_check(
            name="momentum_magnitude_identity",
            error=_max_relative_error(study.electron_pc_kev, expected_pc),
            tolerance=relative_tolerance,
            unit="relative error",
            explanation="Electron momentum is the vector difference of photon momenta.",
        )
    )
    angle_rad = np.radians(study.electron_recoil_angle_deg)
    electron_px = study.electron_pc_kev * np.cos(angle_rad)
    electron_py = study.electron_pc_kev * np.sin(angle_rad)
    checks.append(
        _absolute_check(
            name="x_momentum_conservation",
            error=float(
                np.max(
                    np.abs(
                        study.incident_energy_kev
                        - study.scattered_energy_kev * np.cos(theta_rad)
                        - electron_px
                    )
                    / energy_scale
                )
            ),
            tolerance=conservation_tolerance,
            unit="relative residual",
            explanation="The x component of photon plus electron momentum is conserved.",
        )
    )
    checks.append(
        _absolute_check(
            name="y_momentum_conservation",
            error=float(
                np.max(
                    np.abs(
                        study.scattered_energy_kev * np.sin(theta_rad) - electron_py
                    )
                    / energy_scale
                )
            ),
            tolerance=conservation_tolerance,
            unit="relative residual",
            explanation="Opposite photon/electron y momenta cancel.",
        )
    )
    electron_total_energy = (
        ELECTRON_REST_ENERGY_KEV + study.electron_kinetic_energy_kev
    )
    mass_shell_residual = (
        np.square(electron_total_energy)
        - np.square(study.electron_pc_kev)
        - ELECTRON_REST_ENERGY_KEV**2
    ) / ELECTRON_REST_ENERGY_KEV**2
    checks.append(
        _absolute_check(
            name="electron_mass_shell",
            error=float(np.max(np.abs(mass_shell_residual))),
            tolerance=conservation_tolerance,
            unit="relative residual",
            explanation="The recoiling electron remains on its relativistic mass shell.",
        )
    )

    reference_fields = (
        ("fractional_shift_reference", "fractional_wavelength_shift", study.fractional_wavelength_shift),
        ("scattered_energy_reference", "scattered_energy_kev", study.scattered_energy_kev),
        ("kinetic_energy_reference", "electron_kinetic_energy_kev", study.electron_kinetic_energy_kev),
        ("electron_beta_reference", "electron_beta", study.electron_beta),
        ("electron_momentum_reference", "electron_pc_kev", study.electron_pc_kev),
        ("recoil_angle_reference", "electron_recoil_angle_deg", study.electron_recoil_angle_deg),
    )
    for check_name, field_name, observed in reference_fields:
        expected = _reference_matrix(
            study,
            lambda state, field_name=field_name: float(getattr(state, field_name)),
        )
        checks.append(
            _absolute_check(
                name=check_name,
                error=_max_relative_error(observed, expected),
                tolerance=1.0e-10,
                unit="relative error",
                explanation="Production arrays agree with scalar energy–momentum references.",
            )
        )

    checks.append(
        _absolute_check(
            name="backscatter_fractional_shift",
            error=float(
                np.max(
                    np.abs(
                        study.fractional_wavelength_shift[:, -1]
                        - 2.0 * study.alpha[:, -1]
                    )
                )
            ),
            tolerance=absolute_tolerance,
            unit="dimensionless",
            explanation="Backscatter produces the exact maximum shift 2E/(m_ec^2).",
        )
    )
    expected_right_angle_phi = np.asarray(
        [42.329552359076, 39.906872163848, 35.705015209771, 26.813843232391, 18.684825897744]
    )
    right_angle_index = configuration.angle_point_count // 2
    checks.append(
        _absolute_check(
            name="right_angle_recoil_anchors",
            error=float(
                np.max(
                    np.abs(
                        study.electron_recoil_angle_deg[:, right_angle_index]
                        - expected_right_angle_phi
                    )
                )
            ),
            tolerance=2.0e-11,
            unit="degree",
            explanation="All five independently calculated 90-degree anchors agree.",
        )
    )

    for name, difference, explanation in (
        (
            "fractional_shift_energy_ordering",
            np.diff(study.fractional_wavelength_shift[:, 1:], axis=0),
            "At fixed non-zero angle, higher incident energy gives larger fractional shift.",
        ),
        (
            "electron_speed_energy_ordering",
            np.diff(study.electron_beta[:, 1:], axis=0),
            "At fixed non-zero angle, higher incident energy gives faster recoil.",
        ),
        (
            "recoil_angle_energy_ordering",
            -np.diff(study.electron_recoil_angle_deg[:, 1:-1], axis=0),
            "At fixed interior angle, higher incident energy gives a more forward recoil.",
        ),
    ):
        checks.append(
            _bound_check(
                name=name,
                observed=float(np.min(difference)),
                expected=0.0,
                tolerance=2.0e-13,
                lower=True,
                unit="mixed",
                explanation=explanation,
            )
        )

    return Task09ValidationReport(
        schema_version=VALIDATION_SCHEMA_VERSION,
        study_digest=task09_study_digest(study),
        checks=tuple(checks),
    )


__all__ = [
    "STUDY_ARRAY_FIELDS",
    "Task09ValidationReport",
    "ValidationCheck",
    "task09_study_digest",
    "validate_task09",
]
