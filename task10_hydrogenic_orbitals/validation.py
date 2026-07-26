"""Independent scientific validation for Task 10 hydrogenic orbitals."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from math import factorial, isfinite, pi
from typing import Callable

import numpy as np

from task10_hydrogenic_orbitals.configuration import (
    HydrogenicState,
    official_gallery_states,
)
from task10_hydrogenic_orbitals.constants import CONSTANTS
from task10_hydrogenic_orbitals.models import (
    NumericResult,
    associated_ferrers,
    associated_laguerre,
    effective_bohr_radius_m,
    normalize_density_for_display,
    orbital_energy_ev,
    orbital_summary,
    real_spherical_harmonic,
    scaled_density_cartesian,
    scaled_radial_wavefunction,
    scaled_wavefunction_cartesian,
)
from task10_hydrogenic_orbitals.reference import (
    analytic_1s_scaled_density,
    analytic_2pz_scaled_density,
    analytic_2s_scaled_density,
    reference_associated_ferrers,
    reference_associated_laguerre,
    reference_real_spherical_harmonic,
    reference_scaled_radial_wavefunction,
    reference_scaled_wavefunction_cartesian,
)


VALIDATION_SCHEMA_VERSION = "task10-validation-v1"
POINTWISE_TOLERANCE = 5.0e-13
POLYNOMIAL_REFERENCE_TOLERANCE = 5.0e-12
RADIAL_NORMALIZATION_TOLERANCE = 2.0e-12
ANGULAR_TOLERANCE = 2.0e-12
RADIAL_ORTHOGONALITY_TOLERANCE = 2.0e-11
EXPECTATION_RELATIVE_TOLERANCE = 5.0e-11
SCALING_RELATIVE_TOLERANCE = 5.0e-14
PARITY_TOLERANCE = 5.0e-13


RadialEvaluator = Callable[[HydrogenicState, object], NumericResult]
AngularEvaluator = Callable[[int, int, object, object], NumericResult]
WavefunctionEvaluator = Callable[
    [HydrogenicState, object, object, object], NumericResult
]


@dataclass(frozen=True)
class ValidationCheck:
    """One explicit numerical acceptance condition."""

    name: str
    passed: bool
    maximum_error: float
    tolerance: float
    detail: str


@dataclass(frozen=True)
class Task10ValidationReport:
    """Complete scientific validation report."""

    checks: tuple[ValidationCheck, ...]
    state_digest: str
    schema_version: str = VALIDATION_SCHEMA_VERSION

    @property
    def passed(self) -> bool:
        return all(check.passed for check in self.checks)

    @property
    def failed_checks(self) -> tuple[ValidationCheck, ...]:
        return tuple(check for check in self.checks if not check.passed)


def _supported_states() -> tuple[HydrogenicState, ...]:
    return tuple(
        HydrogenicState(n, l, m)
        for n in range(1, 9)
        for l in range(n)
        for m in range(-l, l + 1)
    )


def _radial_states() -> tuple[HydrogenicState, ...]:
    return tuple(
        HydrogenicState(n, l, 0)
        for n in range(1, 9)
        for l in range(n)
    )


def _angular_states() -> tuple[tuple[int, int], ...]:
    return tuple((l, m) for l in range(8) for m in range(-l, l + 1))


def task10_state_digest() -> str:
    """Hash every supported state and deterministic pointwise anchor."""

    records = []
    points = ((0.17, -0.31, 0.47), (0.73, 1.19, -0.28), (-1.31, 0.83, 2.17))
    for state in _supported_states():
        records.append(
            {
                "state": (
                    state.n,
                    state.l,
                    state.m,
                    state.atomic_number,
                    state.mass_number,
                ),
                "energy_ev": format(orbital_energy_ev(state), ".17g"),
                "radius_m": format(effective_bohr_radius_m(state), ".17g"),
                "wavefunction": [
                    format(
                        float(scaled_wavefunction_cartesian(state, *point)),
                        ".17g",
                    )
                    for point in points
                ],
            }
        )
    encoded = json.dumps(
        {
            "schema": VALIDATION_SCHEMA_VERSION,
            "constants": {
                "electron_mass_kg": format(CONSTANTS.electron_mass_kg, ".17g"),
                "atomic_mass_constant_kg": format(
                    CONSTANTS.atomic_mass_constant_kg, ".17g"
                ),
                "bohr_radius_m": format(CONSTANTS.bohr_radius_m, ".17g"),
                "hartree_energy_ev": format(CONSTANTS.hartree_energy_ev, ".17g"),
            },
            "records": records,
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _maximum_scaled_error(observed: np.ndarray, expected: np.ndarray) -> float:
    scale = np.maximum(1.0, np.abs(expected))
    return float(np.max(np.abs(observed - expected) / scale))


def _relative_error(observed: np.ndarray, expected: np.ndarray) -> float:
    scale = np.maximum(np.finfo(float).tiny, np.abs(expected))
    return float(np.max(np.abs(observed - expected) / scale))


def _numeric_check(
    name: str,
    error: float,
    tolerance: float,
    detail: str,
) -> ValidationCheck:
    return ValidationCheck(
        name=name,
        passed=isfinite(error) and error <= tolerance,
        maximum_error=float(error),
        tolerance=float(tolerance),
        detail=detail,
    )


def _exact_check(name: str, passed: bool, detail: str) -> ValidationCheck:
    return ValidationCheck(
        name=name,
        passed=bool(passed),
        maximum_error=0.0 if passed else 1.0,
        tolerance=0.0,
        detail=detail,
    )


def _laguerre_reference_error() -> float:
    errors = []
    for order in range(8):
        for alpha in range(1, 16, 2):
            for x in (0.0, 0.17, 1.3, 5.9, 17.0):
                observed = float(associated_laguerre(order, alpha, x))
                expected = reference_associated_laguerre(order, alpha, x)
                errors.append(abs(observed - expected) / max(1.0, abs(expected)))
    return max(errors)


def _ferrers_reference_error() -> float:
    errors = []
    for l in range(8):
        for m in range(l + 1):
            for x in (-1.0, -0.73, -0.11, 0.0, 0.38, 0.91, 1.0):
                observed = float(associated_ferrers(l, m, x))
                expected = reference_associated_ferrers(l, m, x)
                errors.append(abs(observed - expected) / max(1.0, abs(expected)))
    return max(errors)


def _radial_reference_error(radial_evaluator: RadialEvaluator) -> float:
    errors = []
    for state in _radial_states():
        for radius in (0.0, 0.03, 0.7, 3.1, 11.0, 37.0, 95.0):
            observed = float(radial_evaluator(state, radius))
            expected = reference_scaled_radial_wavefunction(state, radius)
            errors.append(abs(observed - expected) / max(1.0, abs(expected)))
    return max(errors)


def _angular_reference_error(angular_evaluator: AngularEvaluator) -> float:
    errors = []
    for l, m in _angular_states():
        for polar, azimuth in (
            (0.17, -2.4),
            (0.83, -0.37),
            (1.41, 0.26),
            (2.37, 1.73),
            (2.91, 5.21),
        ):
            observed = float(angular_evaluator(l, m, polar, azimuth))
            expected = reference_real_spherical_harmonic(
                l, m, polar, azimuth
            )
            errors.append(abs(observed - expected) / max(1.0, abs(expected)))
    return max(errors)


def _wavefunction_reference_error(
    wavefunction_evaluator: WavefunctionEvaluator,
) -> float:
    errors = []
    points = (
        (0.0, 0.0, 0.0),
        (0.17, -0.31, 0.47),
        (0.73, 1.19, -0.28),
        (-1.31, 0.83, 2.17),
        (3.7, -2.9, 1.6),
    )
    for state in _supported_states():
        for point in points:
            observed = float(wavefunction_evaluator(state, *point))
            expected = reference_scaled_wavefunction_cartesian(state, *point)
            errors.append(abs(observed - expected) / max(1.0, abs(expected)))
    return max(errors)


def _radial_moments(
    radial_evaluator: RadialEvaluator,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    rho, weights = np.polynomial.laguerre.laggauss(48)
    normalizations = []
    first_moments = []
    second_moments = []
    for state in _radial_states():
        radius = 0.5 * state.n * rho
        radial = np.asarray(radial_evaluator(state, radius))
        base = (
            weights
            * np.exp(rho)
            * radial**2
            * radius**2
            * (0.5 * state.n)
        )
        normalizations.append(float(np.sum(base)))
        first_moments.append(float(np.sum(base * radius)))
        second_moments.append(float(np.sum(base * radius**2)))
    return (
        np.asarray(normalizations),
        np.asarray(first_moments),
        np.asarray(second_moments),
    )


def _angular_gram_matrix(
    angular_evaluator: AngularEvaluator,
) -> np.ndarray:
    cosine, polar_weights = np.polynomial.legendre.leggauss(40)
    azimuth_count = 40
    azimuth = 2.0 * pi * np.arange(azimuth_count) / azimuth_count
    polar = np.arccos(cosine)[:, None]
    azimuth_grid = azimuth[None, :]
    integration_weights = (
        polar_weights[:, None]
        * np.ones((1, azimuth_count))
        * (2.0 * pi / azimuth_count)
    )
    values = np.asarray(
        [
            np.asarray(angular_evaluator(l, m, polar, azimuth_grid)).reshape(-1)
            for l, m in _angular_states()
        ]
    )
    weights_flat = integration_weights.reshape(-1)
    return np.einsum(
        "ik,k,jk->ij", values, weights_flat, values, optimize=True
    )


def _radial_overlap_error(radial_evaluator: RadialEvaluator) -> float:
    nodes, weights = np.polynomial.legendre.leggauss(320)
    maximum_error = 0.0
    for l in range(8):
        states = [HydrogenicState(n, l, 0) for n in range(l + 1, 9)]
        extent = 14.0 * max(state.n for state in states) ** 2
        radius = 0.5 * extent * (nodes + 1.0)
        radial_values = np.asarray(
            [np.asarray(radial_evaluator(state, radius)) for state in states]
        )
        integration_weights = weights * 0.5 * extent * radius**2
        gram = np.einsum(
            "ik,k,jk->ij",
            radial_values,
            integration_weights,
            radial_values,
            optimize=True,
        )
        maximum_error = max(
            maximum_error,
            float(np.max(np.abs(gram - np.eye(len(states))))),
        )
    return maximum_error


def _radial_node_errors(
    radial_evaluator: RadialEvaluator,
) -> tuple[int, float]:
    count_mismatches = 0
    maximum_node_value = 0.0
    for state in _radial_states():
        order = state.radial_node_count
        if order == 0:
            continue
        alpha = 2 * state.l + 1
        coefficients = np.asarray(
            [
                factorial(order + alpha)
                * (-1) ** k
                / (
                    factorial(alpha + k)
                    * factorial(order - k)
                    * factorial(k)
                )
                for k in range(order + 1)
            ],
            dtype=float,
        )
        roots = np.polynomial.polynomial.polyroots(coefficients)
        positive = sorted(
            float(root.real)
            for root in roots
            if abs(root.imag) <= 1e-10 and root.real > 0.0
        )
        if len(positive) != order:
            count_mismatches += 1
            continue
        radii = 0.5 * state.n * np.asarray(positive)
        values = np.asarray(radial_evaluator(state, radii))
        maximum_node_value = max(maximum_node_value, float(np.max(np.abs(values))))
    return count_mismatches, maximum_node_value


def _parity_error(angular_evaluator: AngularEvaluator) -> float:
    errors = []
    for l, m in _angular_states():
        for polar, azimuth in ((0.31, -1.2), (1.17, 0.43), (2.31, 2.7)):
            original = float(angular_evaluator(l, m, polar, azimuth))
            inverted = float(
                angular_evaluator(l, m, pi - polar, azimuth + pi)
            )
            errors.append(abs(inverted - (-1) ** l * original))
    return max(errors)


def _low_state_density_error(
    wavefunction_evaluator: WavefunctionEvaluator,
) -> float:
    errors = []
    state_1s = HydrogenicState(1, 0, 0)
    state_2s = HydrogenicState(2, 0, 0)
    state_2pz = HydrogenicState(2, 1, 0)
    for radius in (0.0, 0.3, 2.0, 5.7):
        density_1s = float(wavefunction_evaluator(state_1s, radius, 0.0, 0.0)) ** 2
        density_2s = float(wavefunction_evaluator(state_2s, radius, 0.0, 0.0)) ** 2
        density_2pz = (
            float(wavefunction_evaluator(state_2pz, 0.0, 0.0, radius)) ** 2
        )
        errors.extend(
            (
                abs(density_1s - analytic_1s_scaled_density(radius)),
                abs(density_2s - analytic_2s_scaled_density(radius)),
                abs(density_2pz - analytic_2pz_scaled_density(radius, 0.0)),
            )
        )
    return max(errors)


def _scaling_errors() -> tuple[float, float]:
    states = (
        HydrogenicState(1, 0, 0, 1, 1),
        HydrogenicState(2, 1, 0, 2, 4),
        HydrogenicState(3, 2, 1, 6, 12),
        HydrogenicState(5, 4, -4, 20, 40),
    )
    energy_invariants = []
    length_invariants = []
    for state in states:
        summary = orbital_summary(state)
        energy_invariants.append(
            summary.energy_ev
            * state.n**2
            / state.atomic_number**2
            / summary.reduced_mass_ratio
        )
        length_invariants.append(
            summary.effective_bohr_radius_m
            * state.atomic_number
            * summary.reduced_mass_ratio
        )
    return (
        _relative_error(
            np.asarray(energy_invariants),
            np.full(len(states), -0.5 * CONSTANTS.hartree_energy_ev),
        ),
        _relative_error(
            np.asarray(length_invariants),
            np.full(len(states), CONSTANTS.bohr_radius_m),
        ),
    )


def validate_task10(
    *,
    radial_evaluator: RadialEvaluator = scaled_radial_wavefunction,
    angular_evaluator: AngularEvaluator = real_spherical_harmonic,
    wavefunction_evaluator: WavefunctionEvaluator = scaled_wavefunction_cartesian,
) -> Task10ValidationReport:
    """Run the complete independent Task 10 scientific acceptance suite."""

    radial_normalization, first_moments, second_moments = _radial_moments(
        radial_evaluator
    )
    radial_states = _radial_states()
    expected_first = np.asarray(
        [
            0.5 * (3 * state.n**2 - state.l * (state.l + 1))
            for state in radial_states
        ]
    )
    expected_second = np.asarray(
        [
            0.5
            * state.n**2
            * (5 * state.n**2 + 1 - 3 * state.l * (state.l + 1))
            for state in radial_states
        ]
    )
    angular_gram = _angular_gram_matrix(angular_evaluator)
    radial_node_mismatches, radial_node_value = _radial_node_errors(
        radial_evaluator
    )
    energy_scaling_error, length_scaling_error = _scaling_errors()
    official_states = official_gallery_states()

    sample_density = np.asarray(
        scaled_density_cartesian(
            HydrogenicState(5, 4, 3),
            np.linspace(-5.0, 5.0, 101),
            0.37,
            -0.81,
        )
    )
    relative_density = np.asarray(normalize_density_for_display(sample_density))

    checks = (
        _exact_check(
            "supported_state_count",
            len(_supported_states()) == 204,
            "all n<=8 real basis states",
        ),
        _exact_check(
            "official_gallery",
            len(official_states) == 25 and len(set(official_states)) == 25,
            "complete 1s/2p/3d/4f/5g gallery",
        ),
        _numeric_check(
            "laguerre_reference",
            _laguerre_reference_error(),
            POLYNOMIAL_REFERENCE_TOLERANCE,
            "recurrence versus official factorial sum",
        ),
        _numeric_check(
            "ferrers_reference",
            _ferrers_reference_error(),
            POINTWISE_TOLERANCE,
            "recurrence versus explicit differentiated Legendre polynomial",
        ),
        _numeric_check(
            "radial_reference",
            _radial_reference_error(radial_evaluator),
            POINTWISE_TOLERANCE,
            "all n,l radial functions at seven radii",
        ),
        _numeric_check(
            "angular_reference",
            _angular_reference_error(angular_evaluator),
            POINTWISE_TOLERANCE,
            "all l,m real harmonics at five nonsymmetric angles",
        ),
        _numeric_check(
            "wavefunction_reference",
            _wavefunction_reference_error(wavefunction_evaluator),
            POINTWISE_TOLERANCE,
            "all 204 states at five Cartesian points",
        ),
        _numeric_check(
            "radial_normalization",
            float(np.max(np.abs(radial_normalization - 1.0))),
            RADIAL_NORMALIZATION_TOLERANCE,
            "36 distinct n,l radial functions",
        ),
        _numeric_check(
            "angular_normalization_and_orthogonality",
            float(np.max(np.abs(angular_gram - np.eye(len(angular_gram))))),
            ANGULAR_TOLERANCE,
            "64 real harmonics through l=7",
        ),
        _numeric_check(
            "radial_orthogonality",
            _radial_overlap_error(radial_evaluator),
            RADIAL_ORTHOGONALITY_TOLERANCE,
            "same-l states through n=8",
        ),
        _numeric_check(
            "mean_radius",
            _relative_error(first_moments, expected_first),
            EXPECTATION_RELATIVE_TOLERANCE,
            "analytic <r>/a for all 36 n,l functions",
        ),
        _numeric_check(
            "mean_square_radius",
            _relative_error(second_moments, expected_second),
            EXPECTATION_RELATIVE_TOLERANCE,
            "analytic <r^2>/a^2 for all 36 n,l functions",
        ),
        _exact_check(
            "radial_node_count",
            radial_node_mismatches == 0,
            "n-l-1 positive Laguerre roots for all radial states",
        ),
        _numeric_check(
            "radial_node_values",
            radial_node_value,
            2.0e-12,
            "production radial function at independent polynomial roots",
        ),
        _numeric_check(
            "angular_parity",
            _parity_error(angular_evaluator),
            PARITY_TOLERANCE,
            "Y(-r)=(-1)^l Y(r) for all real harmonics",
        ),
        _numeric_check(
            "analytic_low_state_densities",
            _low_state_density_error(wavefunction_evaluator),
            POINTWISE_TOLERANCE,
            "closed-form 1s, 2s and 2p_z densities",
        ),
        _numeric_check(
            "energy_scaling",
            energy_scaling_error,
            SCALING_RELATIVE_TOLERANCE,
            "reduced-mass-corrected Z^2/n^2 invariant",
        ),
        _numeric_check(
            "length_scaling",
            length_scaling_error,
            SCALING_RELATIVE_TOLERANCE,
            "reduced-mass-corrected 1/Z invariant",
        ),
        _exact_check(
            "density_bounds",
            bool(np.all(np.isfinite(sample_density)))
            and bool(np.all(sample_density >= 0.0)),
            "sampled density is finite and non-negative",
        ),
        _exact_check(
            "display_normalization_separation",
            bool(np.max(relative_density) == 1.0)
            and bool(np.max(sample_density) != 1.0)
            and not np.shares_memory(sample_density, relative_density),
            "relative display density is a separate immutable result",
        ),
        _exact_check(
            "official_hydrogen_energy",
            abs(orbital_energy_ev(HydrogenicState(1, 0, 0)) + 13.598233405345852)
            <= 5e-14,
            "Z=A=1 ground-state anchor",
        ),
        _exact_check(
            "official_hydrogen_radius",
            abs(
                effective_bohr_radius_m(HydrogenicState(1, 0, 0))
                / CONSTANTS.angstrom_m
                - 0.5294675065300278
            )
            <= 5e-15,
            "Z=A=1 effective Bohr length anchor",
        ),
    )
    return Task10ValidationReport(
        checks=checks,
        state_digest=task10_state_digest(),
    )
