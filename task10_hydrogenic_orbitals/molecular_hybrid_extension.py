"""Superposition, hybrid, molecular and multi-electron extensions for Task 10.

The official explorer displays normalized one-electron Coulomb eigenstates.
This module adds three carefully bounded approximations:

* normalized superpositions and an explicit interpolation between real m
  basis states (a driven morph parameter, not free stationary time evolution);
* orthonormal sp, sp2 and sp3 hybrid combinations plus H2+ LCAO bonding and
  antibonding orbitals; and
* independent-electron, Slater-screened spherical densities for He, Li, C and
  Ne.  These densities integrate to the electron count but omit correlation,
  antisymmetric spin structure and self-consistent orbital relaxation.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike, NDArray

from task10_hydrogenic_orbitals.configuration import HydrogenicState
from task10_hydrogenic_orbitals.constants import CONSTANTS
from task10_hydrogenic_orbitals.models import (
    scaled_radial_wavefunction,
    scaled_wavefunction_cartesian,
)


FloatArray = NDArray[np.float64]
ComplexArray = NDArray[np.complex128]


@dataclass(frozen=True)
class ScreenedSubshell:
    n: int
    l: int
    occupancy: int
    effective_charge: float


SCREENED_ATOMS: dict[str, tuple[ScreenedSubshell, ...]] = {
    "He": (ScreenedSubshell(1, 0, 2, 1.70),),
    "Li": (
        ScreenedSubshell(1, 0, 2, 2.70),
        ScreenedSubshell(2, 0, 1, 1.30),
    ),
    "C": (
        ScreenedSubshell(1, 0, 2, 5.70),
        ScreenedSubshell(2, 0, 2, 3.25),
        ScreenedSubshell(2, 1, 2, 3.25),
    ),
    "Ne": (
        ScreenedSubshell(1, 0, 2, 9.70),
        ScreenedSubshell(2, 0, 2, 5.85),
        ScreenedSubshell(2, 1, 6, 5.85),
    ),
}


def _normalized_coefficients(coefficients: ArrayLike, count: int) -> ComplexArray:
    values = np.asarray(coefficients, dtype=np.complex128)
    if values.shape != (count,) or np.any(~np.isfinite(values)):
        raise ValueError(f"coefficients must be a finite vector of length {count}")
    norm = float(np.sum(np.abs(values) ** 2))
    if norm <= 0.0:
        raise ValueError("at least one coefficient must be non-zero")
    return np.asarray(values / np.sqrt(norm), dtype=np.complex128)


def superposition_wavefunction_scaled(
    states: tuple[HydrogenicState, ...],
    coefficients: ArrayLike,
    x_over_a: ArrayLike,
    y_over_a: ArrayLike,
    z_over_a: ArrayLike,
) -> ComplexArray:
    """Return a normalized linear combination in a common scaled coordinate."""

    if not states or any(not isinstance(state, HydrogenicState) for state in states):
        raise TypeError("states must be a non-empty tuple of HydrogenicState objects")
    identity = {(state.atomic_number, state.mass_number) for state in states}
    if len(identity) != 1:
        raise ValueError("superposed states must share isotope and coordinate scale")
    coefficients_value = _normalized_coefficients(coefficients, len(states))
    result: ComplexArray | None = None
    for coefficient, state in zip(coefficients_value, states):
        basis = np.asarray(
            scaled_wavefunction_cartesian(
                state, x_over_a, y_over_a, z_over_a
            ),
            dtype=np.float64,
        )
        contribution = coefficient * basis
        result = contribution if result is None else result + contribution
    return np.asarray(result, dtype=np.complex128)


def m_state_morph(
    l: int,
    progress: float,
    *,
    n: int | None = None,
) -> tuple[tuple[HydrogenicState, ...], ComplexArray]:
    """Return adjacent-m interpolation coefficients across the full family.

    ``progress`` from zero to one travels from m=-l through every real basis
    state to m=+l using cosine/sine interpolation.  The parameter describes a
    controlled state preparation path, not the free evolution of degenerate
    stationary states.
    """

    if isinstance(l, bool) or int(l) < 1:
        raise ValueError("l must be a positive integer")
    l_value = int(l)
    n_value = l_value + 1 if n is None else int(n)
    if n_value <= l_value:
        raise ValueError("n must exceed l")
    value = float(progress)
    if not np.isfinite(value) or not 0.0 <= value <= 1.0:
        raise ValueError("progress must lie in [0,1]")
    states = tuple(HydrogenicState(n_value, l_value, m) for m in range(-l_value, l_value + 1))
    coefficients = np.zeros(len(states), dtype=np.complex128)
    if value == 1.0:
        coefficients[-1] = 1.0
        return states, coefficients
    coordinate = value * (len(states) - 1)
    left = int(np.floor(coordinate))
    local = coordinate - left
    coefficients[left] = np.cos(0.5 * np.pi * local)
    coefficients[left + 1] = np.sin(0.5 * np.pi * local)
    return states, coefficients


def hybrid_coefficients(kind: str) -> tuple[tuple[HydrogenicState, ...], ComplexArray]:
    """Return orthonormal coefficient rows in the (2s, 2px, 2py, 2pz) basis."""

    basis = (
        HydrogenicState(2, 0, 0),
        HydrogenicState(2, 1, 1),
        HydrogenicState(2, 1, -1),
        HydrogenicState(2, 1, 0),
    )
    normalized = kind.strip().lower()
    if normalized == "sp":
        rows = np.asarray(
            [[1.0, 0.0, 0.0, 1.0], [1.0, 0.0, 0.0, -1.0]],
            dtype=np.float64,
        ) / np.sqrt(2.0)
    elif normalized == "sp2":
        angles = 2.0 * np.pi * np.arange(3) / 3.0
        rows = np.column_stack(
            (
                np.full(3, 1.0 / np.sqrt(3.0)),
                np.sqrt(2.0 / 3.0) * np.cos(angles),
                np.sqrt(2.0 / 3.0) * np.sin(angles),
                np.zeros(3),
            )
        )
    elif normalized == "sp3":
        signs = np.asarray(
            [[1, 1, 1], [1, -1, -1], [-1, 1, -1], [-1, -1, 1]],
            dtype=np.float64,
        )
        rows = np.column_stack((np.full(4, 0.5), 0.5 * signs))
    else:
        raise ValueError("kind must be 'sp', 'sp2', or 'sp3'")
    return basis, np.asarray(rows, dtype=np.complex128)


def hybrid_wavefunctions_scaled(
    kind: str,
    x_over_a: ArrayLike,
    y_over_a: ArrayLike,
    z_over_a: ArrayLike,
) -> ComplexArray:
    """Evaluate every hybrid of one family on a common coordinate grid."""

    basis, coefficient_rows = hybrid_coefficients(kind)
    return np.stack(
        [
            superposition_wavefunction_scaled(
                basis, row, x_over_a, y_over_a, z_over_a
            )
            for row in coefficient_rows
        ],
        axis=0,
    )


def h2plus_overlap(internuclear_separation_over_a0: float) -> float:
    """Return analytic overlap of two hydrogen 1s orbitals separated by R."""

    separation = float(internuclear_separation_over_a0)
    if not np.isfinite(separation) or separation < 0.0:
        raise ValueError("internuclear separation must be finite and non-negative")
    return float(np.exp(-separation) * (1.0 + separation + separation**2 / 3.0))


def h2plus_lcao_wavefunction_scaled(
    x_over_a0: ArrayLike,
    y_over_a0: ArrayLike,
    z_over_a0: ArrayLike,
    internuclear_separation_over_a0: float,
    *,
    bonding: bool = True,
) -> FloatArray:
    """Return normalized H2+ 1s LCAO wavefunction in a0^(-3/2) scale."""

    x, y, z = np.broadcast_arrays(
        np.asarray(x_over_a0, dtype=np.float64),
        np.asarray(y_over_a0, dtype=np.float64),
        np.asarray(z_over_a0, dtype=np.float64),
    )
    if any(np.any(~np.isfinite(value)) for value in (x, y, z)):
        raise ValueError("coordinates must be finite")
    separation = float(internuclear_separation_over_a0)
    overlap = h2plus_overlap(separation)
    radius_a = np.sqrt((x - separation / 2.0) ** 2 + y**2 + z**2)
    radius_b = np.sqrt((x + separation / 2.0) ** 2 + y**2 + z**2)
    orbital_a = np.exp(-radius_a) / np.sqrt(np.pi)
    orbital_b = np.exp(-radius_b) / np.sqrt(np.pi)
    if bonding:
        denominator = np.sqrt(2.0 * (1.0 + overlap))
        return np.asarray((orbital_a + orbital_b) / denominator, dtype=np.float64)
    if separation == 0.0:
        raise ValueError("antibonding state is undefined at zero separation")
    denominator = np.sqrt(2.0 * (1.0 - overlap))
    return np.asarray((orbital_a - orbital_b) / denominator, dtype=np.float64)


def independent_electron_density_m_neg_three(
    element: str,
    radius_m: ArrayLike,
) -> FloatArray:
    """Return Slater-screened spherical independent-electron density."""

    if element not in SCREENED_ATOMS:
        raise ValueError(f"element must be one of {tuple(SCREENED_ATOMS)}")
    radius = np.asarray(radius_m, dtype=np.float64)
    if np.any(~np.isfinite(radius)) or np.any(radius < 0.0):
        raise ValueError("radius_m must be finite and non-negative")
    density = np.zeros(radius.shape, dtype=np.float64)
    for subshell in SCREENED_ATOMS[element]:
        scale = CONSTANTS.bohr_radius_m / subshell.effective_charge
        reference = HydrogenicState(subshell.n, subshell.l, 0)
        radial_scaled = np.asarray(
            scaled_radial_wavefunction(reference, radius / scale),
            dtype=np.float64,
        )
        radial_dimensional = radial_scaled / scale**1.5
        # Summing a completely or spherically averaged subshell over m gives
        # occupancy*|R|^2/(4pi).
        density += subshell.occupancy * radial_dimensional**2 / (4.0 * np.pi)
    return density


def electron_count(element: str) -> int:
    """Return the occupancy represented by one screened atom model."""

    if element not in SCREENED_ATOMS:
        raise ValueError(f"element must be one of {tuple(SCREENED_ATOMS)}")
    return sum(subshell.occupancy for subshell in SCREENED_ATOMS[element])


__all__ = [
    "SCREENED_ATOMS",
    "ScreenedSubshell",
    "electron_count",
    "h2plus_lcao_wavefunction_scaled",
    "h2plus_overlap",
    "hybrid_coefficients",
    "hybrid_wavefunctions_scaled",
    "independent_electron_density_m_neg_three",
    "m_state_morph",
    "superposition_wavefunction_scaled",
]
