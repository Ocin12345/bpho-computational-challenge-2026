"""Independent structured validation for the complete Task 7 study."""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass

import numpy as np

from task07_particle_in_box.analysis import Task07StudyResult
from task07_particle_in_box.configuration import (
    DEFAULT_CONFIGURATION,
    Task07Configuration,
)
from task07_particle_in_box.constants import (
    ELECTRONVOLT_J,
    REDUCED_PLANCK_CONSTANT_J_S,
)
from task07_particle_in_box.reference import (
    reference_energy_j,
    reference_expected_position_squared_m2,
    reference_uncertainty_product_over_hbar,
)


VALIDATION_SCHEMA_VERSION = "task07-validation-v1"


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
class Task07ValidationReport:
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


def task07_study_digest(study: Task07StudyResult) -> str:
    """Return a stable digest of every scientific array in the study."""

    if not isinstance(study, Task07StudyResult):
        raise TypeError("study must be a Task07StudyResult")
    digest = hashlib.sha256(study.schema_version.encode("utf-8"))
    for name in (
        "quantum_numbers",
        "energies_j",
        "energies_ev",
        "energy_ratios",
        "positions_m",
        "density_quantum_numbers",
        "wavefunctions_m_neg_half",
        "probability_densities_m_inv",
        "expected_positions_m",
        "expected_positions_squared_m2",
        "position_uncertainties_m",
        "expected_momenta_kg_m_s",
        "expected_momenta_squared_kg2_m2_s2",
        "momentum_uncertainties_kg_m_s",
        "uncertainty_products_j_s",
        "uncertainty_products_over_hbar",
        "numerical_grid_sizes",
        "numerical_grid_spacings_m",
        "numerical_energies_j",
        "numerical_relative_errors",
        "numerical_convergence_orders",
        "numerical_positions_m",
        "numerical_wavefunctions_m_neg_half",
        "numerical_overlaps",
    ):
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
        error = math.inf
    else:
        error = float(np.max(np.abs((observed - expected) / expected)))
    finite_error = error if math.isfinite(error) else 1.0e300
    return ValidationCheck(
        name=name,
        passed=math.isfinite(error) and error <= tolerance,
        observed=finite_error,
        expected=0.0,
        unit="relative error",
        comparison="relative_error_lte",
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


def _integrate(values: np.ndarray, positions: np.ndarray, axis: int = 0) -> np.ndarray:
    trapezoid = getattr(np, "trapezoid", np.trapz)
    return np.asarray(trapezoid(values, positions, axis=axis), dtype=np.float64)


def validate_task07(
    study: Task07StudyResult,
    configuration: Task07Configuration = DEFAULT_CONFIGURATION,
) -> Task07ValidationReport:
    """Return all pre-declared checks without repairing the study."""

    if not isinstance(study, Task07StudyResult):
        raise TypeError("study must be a Task07StudyResult")
    if not isinstance(configuration, Task07Configuration):
        raise TypeError("configuration must be a Task07Configuration")
    checks: list[ValidationCheck] = []

    expected_n = np.arange(1, configuration.maximum_quantum_number + 1, dtype=np.int64)
    checks.append(
        _exact_check(
            name="quantum_number_enumeration",
            mismatches=int(not np.array_equal(study.quantum_numbers, expected_n)),
            explanation="The energy catalogue contains n=1 through n=10 exactly once.",
        )
    )
    expected_density_n = np.asarray(configuration.density_quantum_numbers, dtype=np.int64)
    checks.append(
        _exact_check(
            name="density_state_enumeration",
            mismatches=int(
                not np.array_equal(study.density_quantum_numbers, expected_density_n)
            ),
            explanation="The approved n=1 to n=4 probability states are present.",
        )
    )
    expected_positions = np.linspace(
        0.0,
        configuration.box_width_m,
        configuration.position_point_count,
        dtype=np.float64,
    )
    checks.append(
        _exact_check(
            name="analytical_position_grid",
            mismatches=int(not np.array_equal(study.positions_m, expected_positions)),
            explanation="The analytical grid includes both boundaries and the midpoint.",
        )
    )

    reference_energies = np.asarray(
        [
            reference_energy_j(
                int(n), configuration.particle_mass_kg, configuration.box_width_m
            )
            for n in expected_n
        ],
        dtype=np.float64,
    )
    checks.append(
        _relative_check(
            name="energy_decimal_reference",
            observed_values=study.energies_j,
            expected_values=reference_energies,
            tolerance=configuration.anchor_relative_tolerance,
            explanation="All energies agree with the independent Decimal h-squared path.",
        )
    )
    checks.append(
        _exact_check(
            name="energy_positive_and_increasing",
            mismatches=int(
                np.count_nonzero(study.energies_j <= 0.0)
                + np.count_nonzero(np.diff(study.energies_j) <= 0.0)
            ),
            explanation="Every energy is positive and strictly increases with n.",
        )
    )
    checks.append(
        _relative_check(
            name="energy_n_squared_scaling",
            observed_values=study.energy_ratios,
            expected_values=np.square(expected_n.astype(np.float64)),
            tolerance=configuration.identity_relative_tolerance,
            explanation="The discrete spectrum satisfies E_n/E_1=n squared.",
        )
    )
    checks.append(
        _relative_check(
            name="electronvolt_conversion",
            observed_values=study.energies_ev,
            expected_values=study.energies_j / ELECTRONVOLT_J,
            tolerance=configuration.identity_relative_tolerance,
            explanation="Joule and electronvolt columns use the exact charge conversion.",
        )
    )

    checks.append(
        _absolute_check(
            name="left_boundary_condition",
            error=float(np.max(np.abs(study.wavefunctions_m_neg_half[0, :]))),
            tolerance=0.0,
            unit="m^-1/2",
            explanation="Every stored eigenfunction is exactly zero at x=0.",
        )
    )
    boundary_scale = math.sqrt(2.0 / configuration.box_width_m)
    checks.append(
        _upper_bound_check(
            name="right_boundary_condition",
            observed=float(
                np.max(np.abs(study.wavefunctions_m_neg_half[-1, :])) / boundary_scale
            ),
            upper_bound=2.0e-15,
            tolerance=0.0,
            unit="relative amplitude",
            explanation="Floating-point sin(n*pi) remains negligible at x=a.",
        )
    )
    checks.append(
        _absolute_check(
            name="born_density_identity",
            error=float(
                np.max(
                    np.abs(
                        study.probability_densities_m_inv
                        - np.square(study.wavefunctions_m_neg_half)
                    )
                )
                * configuration.box_width_m
            ),
            tolerance=configuration.identity_relative_tolerance,
            unit="dimensionless density",
            explanation="Every density is exactly the squared real spatial eigenfunction.",
        )
    )
    checks.append(
        _exact_check(
            name="probability_density_non_negative",
            mismatches=int(np.count_nonzero(study.probability_densities_m_inv < 0.0)),
            explanation="Born probabilities are never negative.",
        )
    )
    norms = _integrate(
        study.probability_densities_m_inv,
        study.positions_m,
        axis=0,
    )
    checks.append(
        _absolute_check(
            name="analytical_normalization",
            error=float(np.max(np.abs(norms - 1.0))),
            tolerance=configuration.integral_absolute_tolerance,
            unit="probability",
            explanation="Each analytical probability density integrates to one.",
        )
    )
    overlap_matrix = np.empty(
        (study.density_quantum_numbers.size, study.density_quantum_numbers.size),
        dtype=np.float64,
    )
    for left in range(study.density_quantum_numbers.size):
        for right in range(study.density_quantum_numbers.size):
            overlap_matrix[left, right] = float(
                _integrate(
                    study.wavefunctions_m_neg_half[:, left]
                    * study.wavefunctions_m_neg_half[:, right],
                    study.positions_m,
                )
            )
    checks.append(
        _absolute_check(
            name="analytical_orthonormality",
            error=float(np.max(np.abs(overlap_matrix - np.eye(overlap_matrix.shape[0])))),
            tolerance=configuration.orthogonality_absolute_tolerance,
            unit="overlap",
            explanation="The stored spatial eigenfunctions are mutually orthonormal.",
        )
    )
    node_error = 0.0
    for n in configuration.density_quantum_numbers:
        if n > 1:
            nodes = configuration.box_width_m * np.arange(1, n, dtype=np.float64) / n
            from task07_particle_in_box.models import spatial_wavefunction_m_neg_half

            node_values = spatial_wavefunction_m_neg_half(
                nodes,
                np.full(nodes.shape, n, dtype=np.int64),
                configuration.box_width_m,
            )
            node_error = max(node_error, float(np.max(np.abs(node_values))) / boundary_scale)
    checks.append(
        _upper_bound_check(
            name="analytical_node_locations",
            observed=node_error,
            upper_bound=2.0e-15,
            tolerance=0.0,
            unit="relative amplitude",
            explanation="State n has its n-1 interior nodes at x=ka/n.",
        )
    )
    checks.append(
        _absolute_check(
            name="density_reflection_symmetry",
            error=float(
                np.max(
                    np.abs(
                        study.probability_densities_m_inv
                        - study.probability_densities_m_inv[::-1, :]
                    )
                )
                * configuration.box_width_m
            ),
            tolerance=5.0e-14,
            unit="dimensionless density",
            explanation="Every stationary density is symmetric about the box midpoint.",
        )
    )

    expected_x = np.full_like(study.expected_positions_m, configuration.box_width_m / 2.0)
    checks.append(
        _relative_check(
            name="expected_position",
            observed_values=study.expected_positions_m,
            expected_values=expected_x,
            tolerance=configuration.identity_relative_tolerance,
            explanation="Every energy eigenstate has mean position a/2.",
        )
    )
    reference_x2 = np.asarray(
        [
            reference_expected_position_squared_m2(int(n), configuration.box_width_m)
            for n in expected_n
        ],
        dtype=np.float64,
    )
    checks.append(
        _relative_check(
            name="expected_position_squared_decimal_reference",
            observed_values=study.expected_positions_squared_m2,
            expected_values=reference_x2,
            tolerance=configuration.anchor_relative_tolerance,
            explanation="Position second moments agree with a high-precision reference.",
        )
    )
    checks.append(
        _relative_check(
            name="position_variance_identity",
            observed_values=np.square(study.position_uncertainties_m),
            expected_values=(
                study.expected_positions_squared_m2
                - np.square(study.expected_positions_m)
            ),
            tolerance=configuration.identity_relative_tolerance,
            explanation="Delta x squared equals the second central moment.",
        )
    )
    checks.append(
        _absolute_check(
            name="expected_momentum_zero",
            error=float(np.max(np.abs(study.expected_momenta_kg_m_s))),
            tolerance=0.0,
            unit="kg m s^-1",
            explanation="Every real standing wave has zero mean momentum.",
        )
    )
    checks.append(
        _relative_check(
            name="momentum_energy_identity",
            observed_values=study.expected_momenta_squared_kg2_m2_s2,
            expected_values=2.0 * configuration.particle_mass_kg * study.energies_j,
            tolerance=configuration.identity_relative_tolerance,
            explanation="Inside the zero-potential well, p squared equals 2mE.",
        )
    )
    checks.append(
        _relative_check(
            name="momentum_uncertainty_identity",
            observed_values=np.square(study.momentum_uncertainties_kg_m_s),
            expected_values=study.expected_momenta_squared_kg2_m2_s2,
            tolerance=configuration.identity_relative_tolerance,
            explanation="Delta p squared equals <p^2> because <p>=0.",
        )
    )
    checks.append(
        _relative_check(
            name="uncertainty_product_factorization",
            observed_values=study.uncertainty_products_j_s,
            expected_values=(
                study.position_uncertainties_m
                * study.momentum_uncertainties_kg_m_s
            ),
            tolerance=configuration.identity_relative_tolerance,
            explanation="The stored uncertainty product equals Delta x times Delta p.",
        )
    )
    reference_products = np.asarray(
        [reference_uncertainty_product_over_hbar(int(n)) for n in expected_n],
        dtype=np.float64,
    )
    checks.append(
        _relative_check(
            name="uncertainty_decimal_reference",
            observed_values=study.uncertainty_products_over_hbar,
            expected_values=reference_products,
            tolerance=configuration.anchor_relative_tolerance,
            explanation="Dimensionless products agree with a 60-digit pi reference.",
        )
    )
    checks.append(
        _lower_bound_check(
            name="heisenberg_uncertainty_bound",
            observed=float(np.min(study.uncertainty_products_over_hbar)),
            lower_bound=0.5,
            tolerance=configuration.identity_relative_tolerance,
            unit="hbar",
            explanation="Every modelled state satisfies Delta x Delta p >= hbar/2.",
        )
    )
    checks.append(
        _relative_check(
            name="ground_state_uncertainty_anchor",
            observed_values=np.asarray([study.ground_uncertainty_over_hbar]),
            expected_values=np.asarray([0.5678618083866119]),
            tolerance=configuration.anchor_relative_tolerance,
            explanation="The ground-state product is the declared 0.567862 hbar anchor.",
        )
    )
    checks.append(
        _exact_check(
            name="uncertainty_product_monotonicity",
            mismatches=int(
                np.count_nonzero(np.diff(study.uncertainty_products_over_hbar) <= 0.0)
            ),
            explanation="The uncertainty product increases strictly over n=1 to 10.",
        )
    )

    expected_grids = np.asarray(configuration.numerical_grid_sizes, dtype=np.int64)
    checks.append(
        _exact_check(
            name="numerical_grid_enumeration",
            mismatches=int(not np.array_equal(study.numerical_grid_sizes, expected_grids)),
            explanation="The complete approved grid-refinement sequence is present.",
        )
    )
    checks.append(
        _relative_check(
            name="numerical_grid_spacing_identity",
            observed_values=study.numerical_grid_spacings_m,
            expected_values=configuration.box_width_m / (expected_grids + 1),
            tolerance=configuration.identity_relative_tolerance,
            explanation="Each Dirichlet grid spacing is a/(N+1).",
        )
    )
    checks.append(
        _exact_check(
            name="numerical_energy_ordering",
            mismatches=int(
                np.count_nonzero(study.numerical_energies_j <= 0.0)
                + np.count_nonzero(np.diff(study.numerical_energies_j, axis=1) <= 0.0)
            ),
            explanation="Every numerical spectrum is positive and ordered.",
        )
    )
    numerical_reference = study.energies_j[: configuration.numerical_state_count]
    calculated_errors = np.abs(
        (study.numerical_energies_j - numerical_reference[None, :])
        / numerical_reference[None, :]
    )
    checks.append(
        _absolute_check(
            name="numerical_error_record_identity",
            error=float(np.max(np.abs(study.numerical_relative_errors - calculated_errors))),
            tolerance=configuration.identity_relative_tolerance,
            unit="relative error",
            explanation="Stored numerical errors are derived from the analytical spectrum.",
        )
    )
    checks.append(
        _upper_bound_check(
            name="finest_grid_energy_accuracy",
            observed=float(np.max(study.numerical_relative_errors[-1, :])),
            upper_bound=configuration.numerical_energy_relative_tolerance,
            tolerance=0.0,
            unit="relative error",
            explanation="The 1600-point grid resolves the first ten energies to target accuracy.",
        )
    )
    checks.append(
        _exact_check(
            name="numerical_error_refinement",
            mismatches=int(
                np.count_nonzero(np.diff(study.numerical_relative_errors, axis=0) >= 0.0)
            ),
            explanation="Every state becomes more accurate whenever the grid is refined.",
        )
    )
    checks.append(
        _lower_bound_check(
            name="finite_difference_convergence_lower",
            observed=float(np.min(study.numerical_convergence_orders)),
            lower_bound=configuration.convergence_order_minimum,
            tolerance=0.0,
            unit="order",
            explanation="Observed energy convergence is at least approximately second order.",
        )
    )
    checks.append(
        _upper_bound_check(
            name="finite_difference_convergence_upper",
            observed=float(np.max(study.numerical_convergence_orders)),
            upper_bound=configuration.convergence_order_maximum,
            tolerance=0.0,
            unit="order",
            explanation="Convergence remains consistent with the central-difference model.",
        )
    )
    checks.append(
        _lower_bound_check(
            name="numerical_eigenfunction_overlap",
            observed=float(np.min(study.numerical_overlaps)),
            lower_bound=configuration.numerical_overlap_minimum,
            tolerance=0.0,
            unit="absolute overlap",
            explanation="Every finest-grid eigenvector matches its analytical state.",
        )
    )
    numerical_dx = configuration.box_width_m / (configuration.numerical_grid_sizes[-1] + 1)
    numerical_gram = (
        study.numerical_wavefunctions_m_neg_half.T
        @ study.numerical_wavefunctions_m_neg_half
        * numerical_dx
    )
    checks.append(
        _absolute_check(
            name="numerical_orthonormality",
            error=float(np.max(np.abs(numerical_gram - np.eye(numerical_gram.shape[0])))),
            tolerance=5.0e-12,
            unit="overlap",
            explanation="The finest-grid numerical eigenvectors are physically normalized.",
        )
    )
    numerical_node_mismatches = 0
    for state_index in range(configuration.numerical_state_count):
        sign_changes = int(
            np.count_nonzero(
                np.diff(np.signbit(study.numerical_wavefunctions_m_neg_half[:, state_index]))
            )
        )
        numerical_node_mismatches += abs(sign_changes - state_index)
    checks.append(
        _exact_check(
            name="numerical_node_counts",
            mismatches=numerical_node_mismatches,
            explanation="The nth numerical eigenstate has n-1 interior sign changes.",
        )
    )

    return Task07ValidationReport(
        schema_version=VALIDATION_SCHEMA_VERSION,
        study_digest=task07_study_digest(study),
        checks=tuple(checks),
    )


__all__ = [
    "Task07ValidationReport",
    "ValidationCheck",
    "task07_study_digest",
    "validate_task07",
]
