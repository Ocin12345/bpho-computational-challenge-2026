"""Normalized radial, angular and Cartesian hydrogenic models."""

from __future__ import annotations

from dataclasses import dataclass
from math import lgamma, pi
from typing import Union

import numpy as np

from task10_hydrogenic_orbitals.configuration import HydrogenicState
from task10_hydrogenic_orbitals.constants import CONSTANTS


NumericResult = Union[float, np.ndarray]


@dataclass(frozen=True)
class HydrogenicStateSummary:
    """Scalar physical properties of one state."""

    state: HydrogenicState
    reduced_mass_kg: float
    reduced_mass_ratio: float
    effective_bohr_radius_m: float
    effective_bohr_radius_angstrom: float
    energy_ev: float
    radial_nodes: int
    angular_nodes: int
    degeneracy: int
    parity: int


def _require_nonnegative_integer(name: str, value: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an integer")
    if value < 0:
        raise ValueError(f"{name} must be non-negative")
    return value


def _finite_array(name: str, value: object) -> np.ndarray:
    try:
        array = np.asarray(value, dtype=float)
    except (TypeError, ValueError) as error:
        raise TypeError(f"{name} must be real numeric data") from error
    if not np.all(np.isfinite(array)):
        raise ValueError(f"{name} must contain only finite values")
    return array


def _finalize(value: object) -> NumericResult:
    array = np.asarray(value, dtype=float)
    if array.ndim == 0:
        return float(array)
    result = np.array(array, dtype=float, copy=True)
    result.setflags(write=False)
    return result


def reduced_mass_kg(state: HydrogenicState) -> float:
    """Return the official reduced mass using M = A u."""

    if not isinstance(state, HydrogenicState):
        raise TypeError("state must be HydrogenicState")
    nuclear_mass = state.mass_number * CONSTANTS.atomic_mass_constant_kg
    return (
        CONSTANTS.electron_mass_kg
        * nuclear_mass
        / (CONSTANTS.electron_mass_kg + nuclear_mass)
    )


def effective_bohr_radius_m(state: HydrogenicState) -> float:
    """Return a = (m_e / mu) a0 / Z."""

    mu = reduced_mass_kg(state)
    return (
        CONSTANTS.electron_mass_kg
        / mu
        * CONSTANTS.bohr_radius_m
        / state.atomic_number
    )


def orbital_energy_ev(state: HydrogenicState) -> float:
    """Return the non-relativistic Coulomb energy."""

    mu_ratio = reduced_mass_kg(state) / CONSTANTS.electron_mass_kg
    return (
        -0.5
        * CONSTANTS.hartree_energy_ev
        * mu_ratio
        * state.atomic_number**2
        / state.n**2
    )


def orbital_summary(state: HydrogenicState) -> HydrogenicStateSummary:
    """Return physical and nodal metadata for one state."""

    mu = reduced_mass_kg(state)
    radius = effective_bohr_radius_m(state)
    return HydrogenicStateSummary(
        state=state,
        reduced_mass_kg=mu,
        reduced_mass_ratio=mu / CONSTANTS.electron_mass_kg,
        effective_bohr_radius_m=radius,
        effective_bohr_radius_angstrom=radius / CONSTANTS.angstrom_m,
        energy_ev=orbital_energy_ev(state),
        radial_nodes=state.radial_node_count,
        angular_nodes=state.angular_node_count,
        degeneracy=2 * state.l + 1,
        parity=(-1) ** state.l,
    )


def associated_laguerre(order: int, alpha: int, x: object) -> NumericResult:
    """Evaluate L_order^alpha(x) with a three-term recurrence."""

    order = _require_nonnegative_integer("order", order)
    alpha = _require_nonnegative_integer("alpha", alpha)
    values = _finite_array("x", x)

    if order == 0:
        return _finalize(np.ones_like(values))
    previous = np.ones_like(values)
    current = 1.0 + alpha - values
    if order == 1:
        return _finalize(current)
    for degree in range(2, order + 1):
        following = (
            (2 * degree - 1 + alpha - values) * current
            - (degree - 1 + alpha) * previous
        ) / degree
        previous, current = current, following
    return _finalize(current)


def associated_ferrers(l: int, m: int, x: object) -> NumericResult:
    """Evaluate the sign-free associated Ferrers function on [-1, 1]."""

    l = _require_nonnegative_integer("l", l)
    m = _require_nonnegative_integer("m", m)
    if m > l:
        raise ValueError("m must not exceed l")
    values = _finite_array("x", x)
    tolerance = 8.0 * np.finfo(float).eps
    if np.any(values < -1.0 - tolerance) or np.any(values > 1.0 + tolerance):
        raise ValueError("x must be in [-1, 1]")
    values = np.clip(values, -1.0, 1.0)

    pmm = np.ones_like(values)
    if m:
        root = np.sqrt(np.maximum(0.0, (1.0 - values) * (1.0 + values)))
        for index in range(1, m + 1):
            pmm = pmm * (2 * index - 1) * root
    if l == m:
        return _finalize(pmm)

    pmmp1 = (2 * m + 1) * values * pmm
    if l == m + 1:
        return _finalize(pmmp1)

    previous, current = pmm, pmmp1
    for degree in range(m + 2, l + 1):
        following = (
            (2 * degree - 1) * values * current
            - (degree + m - 1) * previous
        ) / (degree - m)
        previous, current = current, following
    return _finalize(current)


def _angular_normalization(l: int, m_abs: int) -> float:
    return float(
        np.exp(
            0.5
            * (
                np.log(2 * l + 1)
                - np.log(4 * pi)
                + lgamma(l - m_abs + 1)
                - lgamma(l + m_abs + 1)
            )
        )
    )


def real_spherical_harmonic(
    l: int,
    m: int,
    polar_angle_rad: object,
    azimuth_rad: object,
) -> NumericResult:
    """Evaluate the normalized real tesseral harmonic."""

    l = _require_nonnegative_integer("l", l)
    if isinstance(m, bool) or not isinstance(m, int):
        raise TypeError("m must be an integer")
    if abs(m) > l:
        raise ValueError("m must satisfy -l <= m <= l")

    polar = _finite_array("polar_angle_rad", polar_angle_rad)
    azimuth = _finite_array("azimuth_rad", azimuth_rad)
    tolerance = 8.0 * np.finfo(float).eps
    if np.any(polar < -tolerance) or np.any(polar > pi + tolerance):
        raise ValueError("polar_angle_rad must be in [0, pi]")
    polar = np.clip(polar, 0.0, pi)
    try:
        polar, azimuth = np.broadcast_arrays(polar, azimuth)
    except ValueError as error:
        raise ValueError("polar and azimuth arrays are not broadcast-compatible") from error

    m_abs = abs(m)
    ferrers = np.asarray(associated_ferrers(l, m_abs, np.cos(polar)))
    normalization = _angular_normalization(l, m_abs)
    if m < 0:
        result = (
            np.sqrt(2.0)
            * normalization
            * ferrers
            * np.sin(m_abs * azimuth)
        )
    elif m == 0:
        result = normalization * ferrers
    else:
        result = (
            np.sqrt(2.0)
            * normalization
            * ferrers
            * np.cos(m * azimuth)
        )
    return _finalize(result)


def scaled_radial_wavefunction(
    state: HydrogenicState,
    radius_over_a: object,
) -> NumericResult:
    """Return a^(3/2) R_nl at dimensionless radius r/a."""

    if not isinstance(state, HydrogenicState):
        raise TypeError("state must be HydrogenicState")
    radius = _finite_array("radius_over_a", radius_over_a)
    if np.any(radius < 0.0):
        raise ValueError("radius_over_a must be non-negative")

    order = state.n - state.l - 1
    alpha = 2 * state.l + 1
    rho = 2.0 * radius / state.n
    log_factor = 0.5 * (
        lgamma(order + 1)
        - np.log(2.0 * state.n)
        - lgamma(state.n + state.l + 1)
    )
    prefactor = np.exp(log_factor) * (2.0 / state.n) ** 1.5
    polynomial = np.asarray(associated_laguerre(order, alpha, rho))
    result = (
        prefactor
        * np.exp(-0.5 * rho)
        * np.power(rho, state.l)
        * polynomial
    )
    return _finalize(result)


def radial_wavefunction_m_neg_three_halves(
    state: HydrogenicState,
    radius_m: object,
) -> NumericResult:
    """Return the dimensional radial wavefunction in m^(-3/2)."""

    radius = _finite_array("radius_m", radius_m)
    if np.any(radius < 0.0):
        raise ValueError("radius_m must be non-negative")
    effective_radius = effective_bohr_radius_m(state)
    scaled = np.asarray(scaled_radial_wavefunction(state, radius / effective_radius))
    return _finalize(scaled / effective_radius**1.5)


def cartesian_to_spherical(
    x: object,
    y: object,
    z: object,
) -> tuple[NumericResult, NumericResult, NumericResult]:
    """Convert compatible Cartesian arrays to r, polar colatitude and azimuth."""

    x_values = _finite_array("x", x)
    y_values = _finite_array("y", y)
    z_values = _finite_array("z", z)
    try:
        x_values, y_values, z_values = np.broadcast_arrays(
            x_values, y_values, z_values
        )
    except ValueError as error:
        raise ValueError("Cartesian arrays are not broadcast-compatible") from error
    radius = np.sqrt(x_values**2 + y_values**2 + z_values**2)
    cosine = np.ones_like(radius)
    np.divide(z_values, radius, out=cosine, where=radius > 0.0)
    polar = np.arccos(np.clip(cosine, -1.0, 1.0))
    azimuth = np.arctan2(y_values, x_values)
    return _finalize(radius), _finalize(polar), _finalize(azimuth)


def scaled_wavefunction_cartesian(
    state: HydrogenicState,
    x_over_a: object,
    y_over_a: object,
    z_over_a: object,
) -> NumericResult:
    """Return a^(3/2) psi on dimensionless Cartesian coordinates."""

    radius, polar, azimuth = cartesian_to_spherical(
        x_over_a, y_over_a, z_over_a
    )
    radial = np.asarray(scaled_radial_wavefunction(state, radius))
    angular = np.asarray(
        real_spherical_harmonic(state.l, state.m, polar, azimuth)
    )
    return _finalize(radial * angular)


def scaled_density_cartesian(
    state: HydrogenicState,
    x_over_a: object,
    y_over_a: object,
    z_over_a: object,
) -> NumericResult:
    """Return a^3 |psi|^2 on dimensionless Cartesian coordinates."""

    wavefunction = np.asarray(
        scaled_wavefunction_cartesian(state, x_over_a, y_over_a, z_over_a)
    )
    return _finalize(wavefunction**2)


def density_m_neg_three(
    state: HydrogenicState,
    x_m: object,
    y_m: object,
    z_m: object,
) -> NumericResult:
    """Return physical probability density in m^-3."""

    radius = effective_bohr_radius_m(state)
    x_values = _finite_array("x_m", x_m)
    y_values = _finite_array("y_m", y_m)
    z_values = _finite_array("z_m", z_m)
    scaled = np.asarray(
        scaled_density_cartesian(
            state, x_values / radius, y_values / radius, z_values / radius
        )
    )
    return _finalize(scaled / radius**3)


def scaled_radial_probability(
    state: HydrogenicState,
    radius_over_a: object,
) -> NumericResult:
    """Return the density integrating to one over d(r/a)."""

    radius = _finite_array("radius_over_a", radius_over_a)
    if np.any(radius < 0.0):
        raise ValueError("radius_over_a must be non-negative")
    radial = np.asarray(scaled_radial_wavefunction(state, radius))
    return _finalize(radius**2 * radial**2)


def normalize_density_for_display(density: object) -> NumericResult:
    """Normalize a non-negative density array to its displayed maximum."""

    values = _finite_array("density", density)
    if np.any(values < 0.0):
        raise ValueError("density must be non-negative")
    maximum = float(np.max(values)) if values.size else 0.0
    if maximum <= 0.0:
        raise ValueError("density must contain a positive value")
    return _finalize(values / maximum)
