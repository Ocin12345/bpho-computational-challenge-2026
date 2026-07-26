"""Independent structured validation for the complete Task 6 study."""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass

import numpy as np

from task06_electron_diffraction.analysis import Task06StudyResult
from task06_electron_diffraction.configuration import (
    DEFAULT_CONFIGURATION,
    Task06Configuration,
)
from task06_electron_diffraction.constants import (
    ELECTRON_MASS_KG,
    ELEMENTARY_CHARGE_C,
    INV_SQRT_TWO,
    PLANCK_CONSTANT_J_S,
)
from task06_electron_diffraction.reference import (
    reference_first_order_anchor,
    reference_fit_gradient_v_inv_sqrt,
    reference_maximum_bragg_order,
    reference_maximum_screen_order,
    reference_wavelength_m,
)


VALIDATION_SCHEMA_VERSION = "task06-validation-v1"


@dataclass(frozen=True)
class ValidationCheck:
    """One stable numerical or structural validation result."""

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
            raise ValueError("validation check name must be non-empty text")
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
class Task06ValidationReport:
    """Immutable ordered validation result for one exact Task 6 study."""

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


def task06_study_digest(study: Task06StudyResult) -> str:
    """Return a stable SHA-256 digest of every scientific study field."""

    if not isinstance(study, Task06StudyResult):
        raise TypeError("study must be a Task06StudyResult")
    digest = hashlib.sha256()
    digest.update(study.schema_version.encode("utf-8"))
    array_names = (
        "voltages_v",
        "momenta_kg_m_s",
        "wavelengths_m",
        "spacings_m",
        "maximum_bragg_orders",
        "maximum_screen_orders",
        "voltage_indices",
        "spacing_indices",
        "orders_n",
        "bragg_ratios_q",
        "theta_rad",
        "phi_rad",
        "photo_radii_m",
        "caliper_diameters_m",
        "screen_visible_flags",
    )
    for name in array_names:
        array = np.ascontiguousarray(getattr(study, name))
        digest.update(name.encode("ascii"))
        digest.update(array.dtype.str.encode("ascii"))
        digest.update(str(array.shape).encode("ascii"))
        digest.update(array.tobytes())
    for values in (study.spacing_ids, study.spacing_labels, study.order_statuses):
        digest.update("\x1f".join(values).encode("utf-8"))
    for fit in study.first_order_fits + study.normalized_fits:
        digest.update(repr(fit).encode("utf-8"))
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


def _relative_check(
    *,
    name: str,
    observed_values: np.ndarray,
    expected_values: np.ndarray,
    tolerance: float,
    explanation: str,
) -> ValidationCheck:
    observed = np.asarray(observed_values, dtype=np.float64)
    expected = np.asarray(expected_values, dtype=np.float64)
    if observed.shape != expected.shape or np.any(expected == 0.0):
        relative_error = math.inf
    else:
        relative_error = float(np.max(np.abs((observed - expected) / expected)))
    return ValidationCheck(
        name=name,
        passed=math.isfinite(relative_error) and relative_error <= tolerance,
        observed=relative_error if math.isfinite(relative_error) else 1.0e300,
        expected=0.0,
        unit="relative error",
        comparison="relative_error_lte",
        tolerance=tolerance,
        explanation=explanation,
    )


def _exact_count_check(
    *,
    name: str,
    mismatches: int,
    explanation: str,
) -> ValidationCheck:
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


def validate_task06(
    study: Task06StudyResult,
    configuration: Task06Configuration = DEFAULT_CONFIGURATION,
) -> Task06ValidationReport:
    """Return all pre-declared checks without mutating or repairing the study."""

    if not isinstance(study, Task06StudyResult):
        raise TypeError("study must be a Task06StudyResult")
    if not isinstance(configuration, Task06Configuration):
        raise TypeError("configuration must be a Task06Configuration")

    checks: list[ValidationCheck] = []

    expected_voltages = np.linspace(
        configuration.voltage_min_v,
        configuration.voltage_max_v,
        configuration.voltage_count,
        dtype=np.float64,
    )
    checks.append(
        _exact_count_check(
            name="voltage_enumeration",
            mismatches=int(
                study.voltages_v.shape != expected_voltages.shape
                or not np.array_equal(study.voltages_v, expected_voltages)
            ),
            explanation="The evidence grid is exactly 1000 to 5000 V in 10 V steps.",
        )
    )

    expected_spacings = np.asarray(
        [spacing.spacing_m for spacing in configuration.spacings],
        dtype=np.float64,
    )
    checks.append(
        _exact_count_check(
            name="spacing_catalogue",
            mismatches=int(
                study.spacing_ids
                != tuple(spacing.identifier for spacing in configuration.spacings)
                or study.spacing_labels
                != tuple(spacing.label for spacing in configuration.spacings)
                or not np.array_equal(study.spacings_m, expected_spacings)
            ),
            explanation="Both nominal graphite spacings are present in frozen order.",
        )
    )

    expected_wavelengths = np.asarray(
        [reference_wavelength_m(float(voltage)) for voltage in study.voltages_v],
        dtype=np.float64,
    )
    checks.append(
        _relative_check(
            name="wavelength_decimal_reference",
            observed_values=study.wavelengths_m,
            expected_values=expected_wavelengths,
            tolerance=configuration.identity_relative_tolerance,
            explanation="All wavelengths agree with an independent 60-digit Decimal path.",
        )
    )
    checks.append(
        _exact_count_check(
            name="wavelength_monotonicity",
            mismatches=int(np.count_nonzero(np.diff(study.wavelengths_m) >= 0.0)),
            explanation="Electron wavelength decreases strictly as voltage increases.",
        )
    )
    wavelength_scaling = study.wavelengths_m * np.sqrt(study.voltages_v)
    checks.append(
        _relative_check(
            name="inverse_sqrt_voltage_scaling",
            observed_values=wavelength_scaling,
            expected_values=np.full_like(wavelength_scaling, wavelength_scaling[0]),
            tolerance=configuration.identity_relative_tolerance,
            explanation="lambda times sqrt(V) is constant over the full sweep.",
        )
    )
    energy_observed = np.square(study.momenta_kg_m_s) / (2.0 * ELECTRON_MASS_KG)
    energy_expected = ELEMENTARY_CHARGE_C * study.voltages_v
    checks.append(
        _relative_check(
            name="kinetic_energy_identity",
            observed_values=energy_observed,
            expected_values=energy_expected,
            tolerance=configuration.identity_relative_tolerance,
            explanation="p squared over 2m equals the positive accelerating energy eV.",
        )
    )
    checks.append(
        _relative_check(
            name="de_broglie_identity",
            observed_values=study.momenta_kg_m_s * study.wavelengths_m,
            expected_values=np.full_like(study.wavelengths_m, PLANCK_CONSTANT_J_S),
            tolerance=configuration.identity_relative_tolerance,
            explanation="Every stored momentum and wavelength satisfy p lambda = h.",
        )
    )

    expected_bragg_maximum = np.empty_like(study.maximum_bragg_orders)
    expected_screen_maximum = np.empty_like(study.maximum_screen_orders)
    for voltage_index, voltage in enumerate(study.voltages_v):
        for spacing_index, spacing in enumerate(study.spacings_m):
            expected_bragg_maximum[voltage_index, spacing_index] = (
                reference_maximum_bragg_order(float(voltage), float(spacing))
            )
            expected_screen_maximum[voltage_index, spacing_index] = (
                reference_maximum_screen_order(float(voltage), float(spacing))
            )
    checks.append(
        _exact_count_check(
            name="maximum_bragg_orders",
            mismatches=int(
                np.count_nonzero(study.maximum_bragg_orders != expected_bragg_maximum)
            ),
            explanation="Every official maximum Bragg order matches Decimal flooring.",
        )
    )
    checks.append(
        _exact_count_check(
            name="maximum_screen_orders",
            mismatches=int(
                np.count_nonzero(study.maximum_screen_orders != expected_screen_maximum)
            ),
            explanation="Every forward-screen maximum matches Decimal flooring.",
        )
    )
    checks.append(
        _exact_count_check(
            name="maximum_order_monotonicity",
            mismatches=int(
                np.count_nonzero(np.diff(study.maximum_bragg_orders, axis=0) < 0)
                + np.count_nonzero(np.diff(study.maximum_screen_orders, axis=0) < 0)
            ),
            explanation="Maximum orders never decrease as accelerating voltage rises.",
        )
    )

    expected_catalogue_size = int(np.sum(study.maximum_bragg_orders))
    checks.append(
        _exact_count_check(
            name="catalogue_size",
            mismatches=abs(study.catalogue_size - expected_catalogue_size),
            explanation="The flattened catalogue contains every Bragg order exactly once.",
        )
    )
    expected_rows: list[tuple[int, int, int]] = []
    for voltage_index in range(study.voltages_v.size):
        for spacing_index in range(study.spacings_m.size):
            expected_rows.extend(
                (voltage_index, spacing_index, order)
                for order in range(
                    1,
                    int(study.maximum_bragg_orders[voltage_index, spacing_index]) + 1,
                )
            )
    observed_rows = list(
        zip(
            study.voltage_indices.tolist(),
            study.spacing_indices.tolist(),
            study.orders_n.tolist(),
        )
    )
    checks.append(
        _exact_count_check(
            name="catalogue_ordering",
            mismatches=int(observed_rows != expected_rows),
            explanation="Rows use voltage, spacing, then increasing-order sequence.",
        )
    )

    record_wavelengths = study.wavelengths_m[study.voltage_indices]
    record_spacings = study.spacings_m[study.spacing_indices]
    expected_ratios = study.orders_n.astype(np.float64) * record_wavelengths / (
        2.0 * record_spacings
    )
    checks.append(
        _relative_check(
            name="bragg_ratio_identity",
            observed_values=study.bragg_ratios_q,
            expected_values=expected_ratios,
            tolerance=configuration.identity_relative_tolerance,
            explanation="Every q equals n lambda divided by 2d.",
        )
    )
    checks.append(
        _exact_count_check(
            name="bragg_domain",
            mismatches=int(
                np.count_nonzero(
                    (study.bragg_ratios_q <= 0.0) | (study.bragg_ratios_q > 1.0)
                )
            ),
            explanation="All and only stored orders have 0 < q <= 1.",
        )
    )
    checks.append(
        _absolute_check(
            name="bragg_angle_identity",
            error=float(np.max(np.abs(np.sin(study.theta_rad) - study.bragg_ratios_q))),
            tolerance=configuration.identity_relative_tolerance,
            unit="absolute",
            explanation="Every Bragg angle satisfies sin(theta) = q.",
        )
    )
    checks.append(
        _absolute_check(
            name="scattering_angle_identity",
            error=float(np.max(np.abs(study.phi_rad - 2.0 * study.theta_rad))),
            tolerance=configuration.identity_relative_tolerance,
            unit="rad",
            explanation="Every scattering angle satisfies phi = 2 theta.",
        )
    )
    expected_photo_radii = configuration.tube_radius_m * np.sin(2.0 * study.phi_rad)
    checks.append(
        _absolute_check(
            name="photographic_geometry",
            error=float(np.max(np.abs(study.photo_radii_m - expected_photo_radii))),
            tolerance=configuration.tube_radius_m * configuration.identity_relative_tolerance,
            unit="m",
            explanation="Every photographic radius uses x = r sin(2 phi).",
        )
    )
    expected_caliper = 2.0 * configuration.tube_radius_m * np.sin(study.phi_rad)
    checks.append(
        _absolute_check(
            name="caliper_geometry",
            error=float(np.max(np.abs(study.caliper_diameters_m - expected_caliper))),
            tolerance=configuration.tube_radius_m * configuration.identity_relative_tolerance,
            unit="m",
            explanation="Every caliper diameter uses y = 2r sin(phi).",
        )
    )
    expected_visibility = study.bragg_ratios_q <= INV_SQRT_TWO
    checks.append(
        _exact_count_check(
            name="screen_visibility_classification",
            mismatches=int(
                np.count_nonzero(study.screen_visible_flags != expected_visibility)
            ),
            explanation="Forward-screen records are exactly those with q <= 1/sqrt(2).",
        )
    )
    expected_statuses = tuple(
        "forward_screen" if bool(value) else "back_scattering"
        for value in expected_visibility
    )
    checks.append(
        _exact_count_check(
            name="order_status_labels",
            mismatches=int(study.order_statuses != expected_statuses),
            explanation="Controlled status labels agree with geometric visibility.",
        )
    )
    forward = study.screen_visible_flags
    forward_violations = np.count_nonzero(
        (study.phi_rad[forward] < 0.0)
        | (study.phi_rad[forward] > np.pi / 2.0)
        | (study.photo_radii_m[forward] < -1e-15)
        | (study.photo_radii_m[forward] > configuration.tube_radius_m + 1e-15)
    )
    checks.append(
        _exact_count_check(
            name="forward_screen_bounds",
            mismatches=int(forward_violations),
            explanation="Displayed rings have 0 <= phi <= 90 degrees and 0 <= x <= r.",
        )
    )

    expected_fit_count = configuration.spacing_count
    checks.append(
        _exact_count_check(
            name="fit_record_counts",
            mismatches=(
                abs(len(study.first_order_fits) - expected_fit_count)
                + abs(len(study.normalized_fits) - expected_fit_count)
            ),
            explanation="There is one primary and one normalized fit per spacing.",
        )
    )
    for spacing_index, spacing_definition in enumerate(configuration.spacings):
        spacing_id = spacing_definition.identifier
        primary = study.first_order_fits[spacing_index]
        normalized = study.normalized_fits[spacing_index]
        expected_gradient = reference_fit_gradient_v_inv_sqrt(
            spacing_definition.spacing_m,
            1,
        )
        checks.append(
            _relative_check(
                name=f"{spacing_id}_first_order_gradient",
                observed_values=np.asarray([primary.constrained_gradient_v_inv_sqrt]),
                expected_values=np.asarray([expected_gradient]),
                tolerance=configuration.fit_relative_tolerance,
                explanation=f"{spacing_id} first-order gradient matches the independent formula.",
            )
        )
        checks.append(
            _relative_check(
                name=f"{spacing_id}_first_order_spacing_recovery",
                observed_values=np.asarray([primary.recovered_spacing_m]),
                expected_values=np.asarray([spacing_definition.spacing_m]),
                tolerance=configuration.fit_relative_tolerance,
                explanation=f"{spacing_id} primary fit recovers its nominal atomic spacing.",
            )
        )
        checks.append(
            _absolute_check(
                name=f"{spacing_id}_first_order_intercept",
                error=primary.unconstrained_intercept_v_inv_sqrt,
                tolerance=configuration.fit_intercept_tolerance_v_inv_sqrt,
                unit="V^-1/2",
                explanation=f"{spacing_id} unconstrained diagnostic intercept is zero numerically.",
            )
        )
        checks.append(
            _absolute_check(
                name=f"{spacing_id}_first_order_r_squared",
                error=1.0 - primary.r_squared,
                tolerance=configuration.fit_r_squared_tolerance,
                unit="absolute",
                explanation=f"{spacing_id} primary validation is a straight line.",
            )
        )
        checks.append(
            _relative_check(
                name=f"{spacing_id}_normalized_gradient",
                observed_values=np.asarray([normalized.constrained_gradient_v_inv_sqrt]),
                expected_values=np.asarray([expected_gradient]),
                tolerance=configuration.fit_relative_tolerance,
                explanation=f"{spacing_id} all-order normalized gradient matches first order.",
            )
        )
        checks.append(
            _relative_check(
                name=f"{spacing_id}_normalized_spacing_recovery",
                observed_values=np.asarray([normalized.recovered_spacing_m]),
                expected_values=np.asarray([spacing_definition.spacing_m]),
                tolerance=configuration.fit_relative_tolerance,
                explanation=f"{spacing_id} normalized fit recovers its nominal spacing.",
            )
        )
        family = study.spacing_indices == spacing_index
        family_y = study.orders_n[family].astype(np.float64) / np.sqrt(
            study.voltages_v[study.voltage_indices[family]]
        )
        family_expected = expected_gradient * study.bragg_ratios_q[family]
        normalized_relative_residual = float(
            np.max(np.abs(family_y - family_expected)) / np.max(np.abs(family_y))
        )
        checks.append(
            _absolute_check(
                name=f"{spacing_id}_all_order_collapse",
                error=normalized_relative_residual,
                tolerance=configuration.normalized_residual_relative_tolerance,
                unit="relative residual",
                explanation=f"All {spacing_id} orders collapse onto one normalized line.",
            )
        )

    anchor_mismatches = 0
    anchor_relative_errors: list[float] = []
    for voltage_index in (0, study.voltages_v.size - 1):
        voltage = float(study.voltages_v[voltage_index])
        for spacing_index, spacing in enumerate(study.spacings_m):
            expected_wavelength, expected_phi, expected_radius = reference_first_order_anchor(
                voltage,
                float(spacing),
                configuration.tube_radius_m,
            )
            mask = (
                (study.voltage_indices == voltage_index)
                & (study.spacing_indices == spacing_index)
                & (study.orders_n == 1)
            )
            anchor_mismatches += abs(int(np.count_nonzero(mask)) - 1)
            if np.count_nonzero(mask) == 1:
                anchor_relative_errors.extend(
                    [
                        abs(float(study.wavelengths_m[voltage_index]) / expected_wavelength - 1.0),
                        abs(float(study.phi_rad[mask][0]) / expected_phi - 1.0),
                        abs(float(study.photo_radii_m[mask][0]) / expected_radius - 1.0),
                    ]
                )
    checks.append(
        _exact_count_check(
            name="first_order_anchor_presence",
            mismatches=anchor_mismatches,
            explanation="Each endpoint and spacing has exactly one first-order record.",
        )
    )
    checks.append(
        _absolute_check(
            name="first_order_anchor_values",
            error=max(anchor_relative_errors, default=1.0),
            tolerance=configuration.anchor_relative_tolerance,
            unit="relative error",
            explanation="Endpoint wavelength, angle, and photographic radii match independent anchors.",
        )
    )

    first_order_radius_violations = 0
    for spacing_index in range(study.spacings_m.size):
        mask = (study.spacing_indices == spacing_index) & (study.orders_n == 1)
        ordered_radii = study.photo_radii_m[mask]
        first_order_radius_violations += int(np.count_nonzero(np.diff(ordered_radii) >= 0.0))
    checks.append(
        _exact_count_check(
            name="first_order_ring_contraction",
            mismatches=first_order_radius_violations,
            explanation="Both first-order rings contract strictly over the voltage sweep.",
        )
    )

    return Task06ValidationReport(
        schema_version=VALIDATION_SCHEMA_VERSION,
        study_digest=task06_study_digest(study),
        checks=tuple(checks),
    )


__all__ = [
    "Task06ValidationReport",
    "VALIDATION_SCHEMA_VERSION",
    "ValidationCheck",
    "task06_study_digest",
    "validate_task06",
]
