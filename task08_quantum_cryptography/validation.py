"""Independent structured validation for the complete Task 8 study."""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass

import numpy as np

from task08_quantum_cryptography.analysis import Task08StudyResult
from task08_quantum_cryptography.configuration import (
    DEFAULT_CONFIGURATION,
    Task08Configuration,
)
from task08_quantum_cryptography.models import mismatch_comparison
from task08_quantum_cryptography.reference import (
    REFERENCE_CASES,
    reference_classical_mismatch,
    reference_quantum_mismatch,
)


VALIDATION_SCHEMA_VERSION = "task08-validation-v1"

STUDY_ARRAY_FIELDS = (
    "sweep_theta_deg",
    "sweep_phi_deg",
    "sweep_relative_angle_deg",
    "sweep_detector_a_x",
    "sweep_detector_a_y",
    "sweep_detector_b_x",
    "sweep_detector_b_y",
    "sweep_classical_match",
    "sweep_classical_mismatch",
    "sweep_quantum_match",
    "sweep_quantum_mismatch",
    "sweep_signed_difference",
    "grid_theta_deg",
    "grid_phi_deg",
    "grid_relative_angle_deg",
    "grid_classical_match",
    "grid_classical_mismatch",
    "grid_quantum_match",
    "grid_quantum_mismatch",
    "grid_signed_difference",
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
class Task08ValidationReport:
    """Complete report bound to one immutable study digest."""

    schema_version: str
    study_digest: str
    checks: tuple[ValidationCheck, ...]

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
        names = tuple(check.name for check in checks)
        if len(set(names)) != len(names):
            raise ValueError("validation check names must be unique")
        object.__setattr__(self, "checks", checks)

    @property
    def passed(self) -> bool:
        return all(check.passed for check in self.checks)

    @property
    def failed_checks(self) -> tuple[ValidationCheck, ...]:
        return tuple(check for check in self.checks if not check.passed)


def task08_study_digest(study: Task08StudyResult) -> str:
    """Return a stable digest of every scientific array in the study."""

    if not isinstance(study, Task08StudyResult):
        raise TypeError("study must be a Task08StudyResult")
    digest = hashlib.sha256(study.schema_version.encode("utf-8"))
    for name in STUDY_ARRAY_FIELDS:
        array = np.ascontiguousarray(getattr(study, name))
        digest.update(name.encode("ascii"))
        digest.update(array.dtype.str.encode("ascii"))
        digest.update(str(array.shape).encode("ascii"))
        digest.update(array.tobytes())
    return digest.hexdigest()


def _absolute_check(
    *,
    name: str,
    error: float,
    tolerance: float,
    unit: str,
    explanation: str,
) -> ValidationCheck:
    normalized = abs(float(error))
    if not math.isfinite(normalized):
        normalized = 1.0e300
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
    normalized = int(mismatches)
    return ValidationCheck(
        name=name,
        passed=normalized == 0,
        observed=float(normalized),
        expected=0.0,
        unit="count",
        comparison="exact_equal",
        tolerance=0.0,
        explanation=explanation,
    )


def _lower_bound_check(
    *,
    name: str,
    observed: float,
    lower_bound: float,
    tolerance: float,
    unit: str,
    explanation: str,
) -> ValidationCheck:
    value = float(observed)
    return ValidationCheck(
        name=name,
        passed=value + tolerance >= lower_bound,
        observed=value,
        expected=lower_bound,
        unit=unit,
        comparison="greater_than_or_equal",
        tolerance=tolerance,
        explanation=explanation,
    )


def _upper_bound_check(
    *,
    name: str,
    observed: float,
    upper_bound: float,
    tolerance: float,
    unit: str,
    explanation: str,
) -> ValidationCheck:
    value = float(observed)
    return ValidationCheck(
        name=name,
        passed=value <= upper_bound + tolerance,
        observed=value,
        expected=upper_bound,
        unit=unit,
        comparison="less_than_or_equal",
        tolerance=tolerance,
        explanation=explanation,
    )


def _reference_array(
    theta_deg: np.ndarray,
    phi_deg: np.ndarray,
    function: object,
) -> np.ndarray:
    if function not in (reference_classical_mismatch, reference_quantum_mismatch):
        raise TypeError("function must be a Task 8 scalar reference")
    flat = np.fromiter(
        (
            function(float(theta), float(phi))  # type: ignore[operator]
            for theta, phi in zip(theta_deg.flat, phi_deg.flat)
        ),
        dtype=np.float64,
        count=theta_deg.size,
    )
    return flat.reshape(theta_deg.shape)


def _find_angle_index(values: np.ndarray, target: float, tolerance: float) -> int:
    indices = np.flatnonzero(np.abs(values - target) <= tolerance)
    if indices.size != 1:
        return -1
    return int(indices[0])


def validate_task08(
    study: Task08StudyResult,
    configuration: Task08Configuration = DEFAULT_CONFIGURATION,
) -> Task08ValidationReport:
    """Return all pre-declared checks without repairing the study."""

    if not isinstance(study, Task08StudyResult):
        raise TypeError("study must be a Task08StudyResult")
    if not isinstance(configuration, Task08Configuration):
        raise TypeError("configuration must be a Task08Configuration")

    checks: list[ValidationCheck] = []
    identity_tolerance = configuration.reference_absolute_tolerance
    expected_sweep = np.linspace(
        configuration.angle_minimum_deg,
        configuration.angle_maximum_deg,
        configuration.sweep_point_count,
        dtype=np.float64,
    )
    expected_grid_axis = np.linspace(
        configuration.angle_minimum_deg,
        configuration.angle_maximum_deg,
        configuration.heatmap_point_count,
        dtype=np.float64,
    )
    expected_theta_grid, expected_phi_grid = np.meshgrid(
        expected_grid_axis,
        expected_grid_axis,
        indexing="ij",
    )

    checks.append(
        _absolute_check(
            name="sweep_theta_fixed",
            error=float(
                np.max(np.abs(study.sweep_theta_deg - configuration.official_theta_deg))
            ),
            tolerance=0.0,
            unit="degree",
            explanation="The approved sweep holds detector A at -30 degrees.",
        )
    )
    checks.append(
        _exact_check(
            name="sweep_phi_sampling",
            mismatches=int(not np.array_equal(study.sweep_phi_deg, expected_sweep)),
            explanation="The phi sweep is inclusive, ordered and samples zero.",
        )
    )
    expected_relative = (
        study.sweep_phi_deg - study.sweep_theta_deg + 90.0
    ) % 180.0 - 90.0
    checks.append(
        _absolute_check(
            name="sweep_relative_angle",
            error=float(
                np.max(np.abs(study.sweep_relative_angle_deg - expected_relative))
            ),
            tolerance=0.0,
            unit="degree",
            explanation="Relative detector angles use the frozen 180-degree convention.",
        )
    )
    checks.append(
        _exact_check(
            name="grid_theta_sampling",
            mismatches=int(not np.array_equal(study.grid_theta_deg, expected_theta_grid)),
            explanation="Every grid row has the approved theta coordinate.",
        )
    )
    checks.append(
        _exact_check(
            name="grid_phi_sampling",
            mismatches=int(not np.array_equal(study.grid_phi_deg, expected_phi_grid)),
            explanation="Every grid column has the approved phi coordinate.",
        )
    )
    checks.append(
        _exact_check(
            name="all_scientific_arrays_finite",
            mismatches=sum(
                int(np.count_nonzero(~np.isfinite(getattr(study, name))))
                for name in STUDY_ARRAY_FIELDS
            ),
            explanation="Every stored angle and probability is finite.",
        )
    )

    for detector_name, x_values, y_values in (
        ("a", study.sweep_detector_a_x, study.sweep_detector_a_y),
        ("b", study.sweep_detector_b_x, study.sweep_detector_b_y),
    ):
        checks.append(
            _absolute_check(
                name=f"sweep_detector_{detector_name}_normalized",
                error=float(np.max(np.abs(x_values + y_values - 1.0))),
                tolerance=identity_tolerance,
                unit="probability",
                explanation=f"Detector {detector_name.upper()} X/Y outcomes sum to one.",
            )
        )

    for scope, classical_match, classical_mismatch, quantum_match, quantum_mismatch in (
        (
            "sweep",
            study.sweep_classical_match,
            study.sweep_classical_mismatch,
            study.sweep_quantum_match,
            study.sweep_quantum_mismatch,
        ),
        (
            "grid",
            study.grid_classical_match,
            study.grid_classical_mismatch,
            study.grid_quantum_match,
            study.grid_quantum_mismatch,
        ),
    ):
        checks.append(
            _absolute_check(
                name=f"{scope}_classical_complement",
                error=float(np.max(np.abs(classical_match + classical_mismatch - 1.0))),
                tolerance=identity_tolerance,
                unit="probability",
                explanation=f"Classical match and mismatch complement on the {scope}.",
            )
        )
        checks.append(
            _absolute_check(
                name=f"{scope}_quantum_complement",
                error=float(np.max(np.abs(quantum_match + quantum_mismatch - 1.0))),
                tolerance=identity_tolerance,
                unit="probability",
                explanation=f"Quantum match and mismatch complement on the {scope}.",
            )
        )

    reference_sweep_classical = _reference_array(
        study.sweep_theta_deg,
        study.sweep_phi_deg,
        reference_classical_mismatch,
    )
    reference_sweep_quantum = _reference_array(
        study.sweep_theta_deg,
        study.sweep_phi_deg,
        reference_quantum_mismatch,
    )
    reference_grid_classical = _reference_array(
        study.grid_theta_deg,
        study.grid_phi_deg,
        reference_classical_mismatch,
    )
    reference_grid_quantum = _reference_array(
        study.grid_theta_deg,
        study.grid_phi_deg,
        reference_quantum_mismatch,
    )
    for name, observed, expected in (
        ("sweep_classical_double_angle_reference", study.sweep_classical_mismatch, reference_sweep_classical),
        ("sweep_quantum_double_angle_reference", study.sweep_quantum_mismatch, reference_sweep_quantum),
        ("grid_classical_double_angle_reference", study.grid_classical_mismatch, reference_grid_classical),
        ("grid_quantum_double_angle_reference", study.grid_quantum_mismatch, reference_grid_quantum),
    ):
        checks.append(
            _absolute_check(
                name=name,
                error=float(np.max(np.abs(observed - expected))),
                tolerance=identity_tolerance,
                unit="probability",
                explanation="The production equation agrees with its independent double-angle form.",
            )
        )

    official_index = _find_angle_index(
        study.sweep_phi_deg,
        configuration.official_phi_deg,
        identity_tolerance,
    )
    if official_index < 0:
        official_classical = official_quantum = official_difference = 1.0e300
    else:
        official_classical = float(study.sweep_classical_mismatch[official_index])
        official_quantum = float(study.sweep_quantum_mismatch[official_index])
        official_difference = float(study.sweep_signed_difference[official_index])
    for name, observed, expected in (
        ("official_classical_anchor", official_classical, 3.0 / 8.0),
        ("official_quantum_anchor", official_quantum, 3.0 / 4.0),
        ("official_difference_anchor", official_difference, 3.0 / 8.0),
    ):
        checks.append(
            _absolute_check(
                name=name,
                error=observed - expected,
                tolerance=identity_tolerance,
                unit="probability",
                explanation="The official -30/+30 degree worked example is reproduced.",
            )
        )

    case_classical_errors: list[float] = []
    case_quantum_errors: list[float] = []
    case_difference_errors: list[float] = []
    for case in REFERENCE_CASES:
        result = mismatch_comparison(case.theta_deg, case.phi_deg)
        case_classical_errors.append(
            abs(float(result.classical_mismatch) - float(case.classical_mismatch))
        )
        case_quantum_errors.append(
            abs(float(result.quantum_mismatch) - float(case.quantum_mismatch))
        )
        case_difference_errors.append(
            abs(float(result.signed_difference) - float(case.signed_difference))
        )
    for name, errors in (
        ("exact_cases_classical", case_classical_errors),
        ("exact_cases_quantum", case_quantum_errors),
        ("exact_cases_difference", case_difference_errors),
    ):
        checks.append(
            _absolute_check(
                name=name,
                error=max(errors),
                tolerance=identity_tolerance,
                unit="probability",
                explanation="All exact rational reference cases agree with the model.",
            )
        )

    checks.extend(
        (
            _lower_bound_check(
                name="classical_probability_lower_bound",
                observed=float(np.min(study.grid_classical_mismatch)),
                lower_bound=0.0,
                tolerance=identity_tolerance,
                unit="probability",
                explanation="Classical mismatch never falls below zero.",
            ),
            _upper_bound_check(
                name="classical_probability_upper_bound",
                observed=float(np.max(study.grid_classical_mismatch)),
                upper_bound=1.0,
                tolerance=identity_tolerance,
                unit="probability",
                explanation="Classical mismatch never exceeds one.",
            ),
            _lower_bound_check(
                name="quantum_probability_lower_bound",
                observed=float(np.min(study.grid_quantum_mismatch)),
                lower_bound=0.0,
                tolerance=identity_tolerance,
                unit="probability",
                explanation="Quantum mismatch never falls below zero.",
            ),
            _upper_bound_check(
                name="quantum_probability_upper_bound",
                observed=float(np.max(study.grid_quantum_mismatch)),
                upper_bound=1.0,
                tolerance=identity_tolerance,
                unit="probability",
                explanation="Quantum mismatch never exceeds one.",
            ),
            _lower_bound_check(
                name="difference_lower_bound",
                observed=float(np.min(study.grid_signed_difference)),
                lower_bound=-0.5,
                tolerance=identity_tolerance,
                unit="probability",
                explanation="Quantum-minus-classical contrast is no smaller than -0.5.",
            ),
            _upper_bound_check(
                name="difference_upper_bound",
                observed=float(np.max(study.grid_signed_difference)),
                upper_bound=0.5,
                tolerance=identity_tolerance,
                unit="probability",
                explanation="Quantum-minus-classical contrast is no larger than +0.5.",
            ),
            _absolute_check(
                name="difference_negative_extremum",
                error=float(np.min(study.grid_signed_difference)) + 0.5,
                tolerance=identity_tolerance,
                unit="probability",
                explanation="The approved grid reaches the -0.5 contrast configuration.",
            ),
            _absolute_check(
                name="difference_positive_extremum",
                error=float(np.max(study.grid_signed_difference)) - 0.5,
                tolerance=identity_tolerance,
                unit="probability",
                explanation="The approved grid reaches the +0.5 contrast configuration.",
            ),
        )
    )

    for scope, difference, quantum, classical in (
        ("sweep", study.sweep_signed_difference, study.sweep_quantum_mismatch, study.sweep_classical_mismatch),
        ("grid", study.grid_signed_difference, study.grid_quantum_mismatch, study.grid_classical_mismatch),
    ):
        checks.append(
            _absolute_check(
                name=f"{scope}_signed_difference_identity",
                error=float(np.max(np.abs(difference - (quantum - classical)))),
                tolerance=0.0,
                unit="probability",
                explanation=f"Stored {scope} contrast equals quantum minus classical mismatch.",
            )
        )

    checks.append(
        _absolute_check(
            name="classical_swap_symmetry",
            error=float(
                np.max(
                    np.abs(
                        study.grid_classical_mismatch
                        - study.grid_classical_mismatch.T
                    )
                )
            ),
            tolerance=identity_tolerance,
            unit="probability",
            explanation="The classical result is unchanged when detectors are exchanged.",
        )
    )
    checks.append(
        _absolute_check(
            name="quantum_swap_symmetry",
            error=float(
                np.max(
                    np.abs(
                        study.grid_quantum_mismatch
                        - study.grid_quantum_mismatch.T
                    )
                )
            ),
            tolerance=identity_tolerance,
            unit="probability",
            explanation="The quantum result is unchanged when detectors are exchanged.",
        )
    )

    probe_theta = np.asarray([-73.5, -30.0, 0.0, 19.25, 87.0])
    probe_phi = np.asarray([62.0, 30.0, -45.0, 81.75, -88.0])
    baseline = mismatch_comparison(probe_theta, probe_phi)
    shifted = mismatch_comparison(probe_theta + 180.0, probe_phi - 360.0)
    checks.append(
        _absolute_check(
            name="classical_periodicity",
            error=float(
                np.max(
                    np.abs(
                        baseline.classical_mismatch - shifted.classical_mismatch
                    )
                )
            ),
            tolerance=identity_tolerance,
            unit="probability",
            explanation="Classical probabilities are invariant under 180-degree axis shifts.",
        )
    )
    checks.append(
        _absolute_check(
            name="quantum_periodicity",
            error=float(
                np.max(np.abs(baseline.quantum_mismatch - shifted.quantum_mismatch))
            ),
            tolerance=identity_tolerance,
            unit="probability",
            explanation="Quantum probabilities are invariant under 180-degree axis shifts.",
        )
    )
    checks.append(
        _absolute_check(
            name="quantum_equal_angle_zero",
            error=float(np.max(np.abs(np.diag(study.grid_quantum_mismatch)))),
            tolerance=identity_tolerance,
            unit="probability",
            explanation="Equal detector settings produce zero quantum mismatch.",
        )
    )

    theta_index = _find_angle_index(
        expected_grid_axis,
        configuration.official_theta_deg,
        identity_tolerance,
    )
    phi_index = _find_angle_index(
        expected_grid_axis,
        configuration.official_phi_deg,
        identity_tolerance,
    )
    if theta_index < 0 or phi_index < 0:
        grid_classical = grid_quantum = grid_difference = 1.0e300
    else:
        grid_classical = float(study.grid_classical_mismatch[theta_index, phi_index])
        grid_quantum = float(study.grid_quantum_mismatch[theta_index, phi_index])
        grid_difference = float(study.grid_signed_difference[theta_index, phi_index])
    for name, observed, expected in (
        ("grid_official_classical", grid_classical, 3.0 / 8.0),
        ("grid_official_quantum", grid_quantum, 3.0 / 4.0),
        ("grid_official_difference", grid_difference, 3.0 / 8.0),
    ):
        checks.append(
            _absolute_check(
                name=name,
                error=observed - expected,
                tolerance=identity_tolerance,
                unit="probability",
                explanation="The full grid independently contains the official example.",
            )
        )

    checks.append(
        _absolute_check(
            name="sweep_spacing",
            error=float(np.max(np.abs(np.diff(study.sweep_phi_deg) - configuration.sweep_spacing_deg))),
            tolerance=identity_tolerance,
            unit="degree",
            explanation="The one-dimensional sweep has uniform 0.5-degree spacing.",
        )
    )
    checks.append(
        _absolute_check(
            name="grid_spacing",
            error=max(
                float(np.max(np.abs(np.diff(study.grid_theta_deg[:, 0]) - configuration.heatmap_spacing_deg))),
                float(np.max(np.abs(np.diff(study.grid_phi_deg[0, :]) - configuration.heatmap_spacing_deg))),
            ),
            tolerance=identity_tolerance,
            unit="degree",
            explanation="Both heatmap axes have uniform one-degree spacing.",
        )
    )

    return Task08ValidationReport(
        schema_version=VALIDATION_SCHEMA_VERSION,
        study_digest=task08_study_digest(study),
        checks=tuple(checks),
    )


__all__ = [
    "STUDY_ARRAY_FIELDS",
    "Task08ValidationReport",
    "VALIDATION_SCHEMA_VERSION",
    "ValidationCheck",
    "task08_study_digest",
    "validate_task08",
]
